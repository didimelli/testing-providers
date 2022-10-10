from functools import wraps

from distmqtt.broker import create_broker


def mqtt_brokered(fn):
    """Opens a localhost mqtt broker."""

    @wraps(fn)
    async def apply_broker(*args, **kwargs):
        async with create_broker():
            return await fn(*args, **kwargs)

    return apply_broker
