# docker-compose example

Runs websocket-test image behind an nginx proxy.
Contains two proxy configurations, one that works, one that doesn't.
The

Run with:

```
docker compose up
```

in this directory.

http://localhost:9000 will serve a page where websockets work,
while http://localhost:9090 will not.

