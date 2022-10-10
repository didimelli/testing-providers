"""Tests trio functionalities."""


import logging

import pytest
from anyio import EndOfStream
from anyio.abc import SocketStream
from distmqtt.client import MQTTClient
from distmqtt.client import open_mqttclient
from distmqtt.session import IncomingApplicationMessage
from trio import TASK_STATUS_IGNORED
from trio import MemoryReceiveChannel
from trio import MemorySendChannel
from trio import open_memory_channel
from trio import open_nursery
from trio import open_tcp_stream
from trio_websocket import ConnectionClosed
from trio_websocket import WebSocketConnection
from trio_websocket import WebSocketRequest
from trio_websocket import open_websocket_url

from testing_providers.mqtt import mqtt_brokered
from testing_providers.tcp import tcp_served
from testing_providers.ws import ws_served


async def echo_tcp(stream: SocketStream) -> None:
    """TCP echo server."""
    try:
        while True:
            msg = await stream.receive()
            await stream.send(msg)
    except EndOfStream:
        # client disconnected!
        logging.warning("Client disconnected!")
        return


@pytest.mark.trio
@tcp_served(12345, echo_tcp)
async def test_tcp() -> None:
    """Tests the `tcp_served` decorator."""
    async with await open_tcp_stream("127.0.0.1", 12345) as stream:
        await stream.send_all(b"test1")
        assert await stream.receive_some() == b"test1"
        await stream.send_all(b"test2")
        assert await stream.receive_some() == b"test2"
        await stream.send_all(b"test3")
        assert await stream.receive_some() == b"test3"
        await stream.send_all(b"test4")
        assert await stream.receive_some() == b"test4"


@pytest.mark.trio
@mqtt_brokered
async def test_mqtt() -> None:
    """Tests the `mqtt_brokered` decorator."""

    async def publisher(mqtt_client: MQTTClient) -> None:
        """Publishes data to mqtt broker."""
        await mqtt_client.publish("/topic", b"first")
        await mqtt_client.publish("/topic", b"second")
        await mqtt_client.publish("/topic", b"third")
        await mqtt_client.publish("/topic", b"fourth")

    async def subscriber(
        mqtt_client: MQTTClient,
        mem_send_chan: MemorySendChannel,
        *,
        task_status=TASK_STATUS_IGNORED
    ) -> None:
        """Received data from subscribtion and put them inside memory
        channel."""
        msg: IncomingApplicationMessage
        async with mqtt_client.subscription("/topic") as subscription:
            task_status.started()
            async for msg in subscription:
                await mem_send_chan.send(msg)  # type: ignore

    async with open_mqttclient("mqtt://127.0.0.1:1883") as mqtt_client:
        async with open_nursery() as n:
            mem_recv_chan: MemoryReceiveChannel
            mem_send_chan: MemorySendChannel
            mem_send_chan, mem_recv_chan = open_memory_channel(10)
            await n.start(subscriber, mqtt_client, mem_send_chan)
            # waits for the subscriber to be ready to get messages
            n.start_soon(publisher, mqtt_client)
            first: IncomingApplicationMessage = await mem_recv_chan.receive()  # type: ignore # noqa: E501
            assert first.data == b"first"
            second: IncomingApplicationMessage = await mem_recv_chan.receive()  # type: ignore # noqa: E501
            assert second.data == b"second"
            third: IncomingApplicationMessage = await mem_recv_chan.receive()  # type: ignore # noqa: E501
            assert third.data == b"third"
            fourth: IncomingApplicationMessage = await mem_recv_chan.receive()  # type: ignore # noqa: E501
            assert fourth.data == b"fourth"
            n.cancel_scope.cancel()


async def echo_ws(request: WebSocketRequest):
    """WS echo server."""
    ws: WebSocketConnection = await request.accept()
    try:
        while True:
            msg = await ws.get_message()
            print(msg)
            await ws.send_message(msg)
    except ConnectionClosed:
        pass


@pytest.mark.trio
@ws_served(12345, echo_ws)
async def test_ws() -> None:
    """Tests the `ws_served` decorator."""
    ws: WebSocketConnection
    async with open_websocket_url("ws://127.0.0.1:12345") as ws:
        await ws.send_message(b"first")
        assert await ws.get_message() == b"first"
        await ws.send_message(b"second")
        assert await ws.get_message() == b"second"
        await ws.send_message(b"third")
        assert await ws.get_message() == b"third"
        await ws.send_message(b"fourth")
        assert await ws.get_message() == b"fourth"
