import asyncio
import logging
import pprint
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from websockets.asyncio.client import connect as websocket_connect

app_dir = Path(__file__).parent.resolve()
test_html = app_dir / "test.html"
app = FastAPI()

log = logging.getLogger("uvicorn.error")


@app.get("/")
async def get():
    with test_html.open() as f:
        return HTMLResponse(f.read())


def get_subprotocols(websocket: WebSocket) -> list[str]:
    subprotocol_header = websocket.headers.get("Sec-Websocket-Protocol")
    if not subprotocol_header:
        return None
    return [s.strip() for s in subprotocol_header.split(",")]


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    subprotocols = get_subprotocols(websocket)
    accepted_subprotocols = [s for s in subprotocols or [] if "ignored" not in s]
    subprotocol = accepted_subprotocols[0] if accepted_subprotocols else None
    headers = pprint.pformat(dict(websocket.headers))
    log.info("Backend websocket headers: %s", headers)
    log.info(f"Accepting websocket with {subprotocol}")
    await websocket.accept(subprotocol)
    async def echo():
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Reply: {data}")
    async def stream():
        while True:
            await websocket.send_text("alive...")
            await asyncio.sleep(3)
    tasks = [asyncio.create_task(echo()), asyncio.create_task(stream())]
    try:
        await asyncio.gather(*tasks)
    except WebSocketDisconnect:
        log.info("backend websocket closed")
        [t.cancel() for t in tasks if not t.done()]


@app.websocket("/ws-proxy")
async def ws_proxy(websocket: WebSocket):
    log.info("Proxy websocket headers: %s", pprint.pformat(dict(websocket.headers)))
    subprotocols = get_subprotocols(websocket)
    log.info("Proxy websocket requested subprotocols: %s", subprotocols)
    # hop once
    url = "ws://127.0.0.1:8000/ws"
    hop_by_hop_headers = {
        "proxy-connection",
        "keep-alive",
        "transfer-encoding",
        "te",
        "connection",
        "trailer",
        "upgrade",
        "proxy-authorization",
        "proxy-authenticate",
    }
    passthrough_headers = {
        h: value
        for h, value in websocket.headers.items()
        if h.lower() not in hop_by_hop_headers
        and not h.lower().startswith("sec-websocket-")
    }
    log.info(
        "Passing through websocket headers: %s", pprint.pformat(passthrough_headers)
    )
    async with websocket_connect(
        url, subprotocols=subprotocols, additional_headers=passthrough_headers
    ) as upstream:
        log.info(f"Accepting proxy websocket with {upstream.subprotocol}")
        await websocket.accept(upstream.subprotocol)

        async def proxy_up():
            while True:
                data = await websocket.receive_text()
                await upstream.send(data)

        async def proxy_down():
            while True:
                reply = await upstream.recv()
                await websocket.send_text(reply)

        tasks = [asyncio.create_task(proxy_up()), asyncio.create_task(proxy_down())]
        try:
            await asyncio.gather(*tasks)
        except WebSocketDisconnect:
            log.info("proxy websocket closed")
            [t.cancel() for t in tasks if not t.done()]
