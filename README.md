# websocket test

A simple test application for debugging websocket support in proxies.

Run the image `ghcr.io/minrk/websocket-proxy-test` exposing port 8000 and place it behind your proxy to test your proxy implementation.

e.g.

```
docker run --rm -it -p 127.0.0.1:8000:8000 ghcr.io/minrk/websocket-proxy-test
```

It serves a simple HTML page for websocket testing and logs debugging information about requests.

Visit your proxied page to test your websockets.

The backend itself implements its own websocket proxy for further testing.

There is an example proxy test using `docker compose` in the examples directory.
