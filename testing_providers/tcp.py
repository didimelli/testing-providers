from functools import wraps
from typing import Any
from typing import Callable
from typing import Coroutine

from anyio import TASK_STATUS_IGNORED
from anyio import create_task_group
from anyio import create_tcp_listener
from anyio.abc import TaskStatus


def tcp_served(port: int, handler: Callable[..., Coroutine[Any, Any, Any]]):
    """Opens a localhost tcp server at the defined port with the defined
    handler."""

    def serve(fn):
        @wraps(fn)
        async def open_tcp_server(*args, **kwargs):
            async def create_listener(
                port: int, *, task_status: TaskStatus = TASK_STATUS_IGNORED
            ) -> None:
                listener = await create_tcp_listener(local_port=port)
                task_status.started()
                await listener.serve(handler)

            async with create_task_group() as tg:
                await tg.start(create_listener, port)
                res = await fn(*args, **kwargs)
                tg.cancel_scope.cancel()
            return res

        return open_tcp_server

    return serve
