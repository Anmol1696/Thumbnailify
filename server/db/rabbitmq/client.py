import logging
import aioamqp

from ...exceptions import DBError

logger = logging.getLogger("aiohttp.application")


class Client:
    _transport = None
    _protocol = None
    channel = None
    queue_name = None

    @classmethod
    async def setup(cls, config):
        cls.queue_name = config.get("name", "default_task")
        cls._transport, cls._protocol = await aioamqp.connect(**config)
        cls.channel = await cls._protocol.channel()
        await cls.channel.queue_declare(cls.queue_name, durable=True)

    @classmethod
    async def add_task(cls, payload, **kwargs):
        try:
            await cls.channel.basic_publish(
                payload=payload,
                exchange_name="",
                routing_key=cls.queue_name,
                properties={
                    "headers": kwargs,
                    "delivery_mode": 2,
                },
            )
        except Exception as e:
            logger.exception(f"Error sending data, `{payload}`")
            raise DBError
        logger.info(f"Added `{payload}` to queue `{cls.queue_name}` with headers `{kwargs}`")

    @classmethod
    async def close(cls):
        await cls.protocol.close()
        cls.transport.close()
