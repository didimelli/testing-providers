# Testing providers

To wrap an async function in an async provider.
Very useful to test network interfaces or to test applications mocking outer services.

## Supported providers

- [x] MQTT broker (anyio)
- [x] TCP server (anyio)
- [x] WebSocket server (trio)
- [ ] WebSocket server (asyncio)
