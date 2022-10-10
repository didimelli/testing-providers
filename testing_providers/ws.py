from functools import wraps
from typing import Any
from typing import Callable
from typing import Coroutine

from anyio import create_task_group
from trio_websocket import serve_websocket


def ws_served(port: int, handler: Callable[..., Coroutine[Any, Any, Any]]):
    """Opens a local ws server at the defined port with the defined
    handler."""

    def serve(fn):
        @wraps(fn)
        async def open_ws_server(*args, **kwargs):
            async with create_task_group() as tg:
                await tg.start(serve_websocket, handler, "127.0.0.1", port, None)
                res = await fn(*args, **kwargs)
                tg.cancel_scope.cancel()
            return res

        return open_ws_server

    return serve
