import logging
import aioredis

from ...exceptions import DBError

logger = logging.getLogger("aiohttp.application")


class Client:
    """
    State management class, using redis key value pair
    """
    transport = None

    @classmethod
    async def setup(cls, config):
        host = config.pop("host")
        port = config.pop("port")
        cls.transport = await aioredis.create_redis((host, port), **config)
        return cls

    @classmethod
    async def update_state(cls, media_id, **data):
        try:
            await cls.transport.hmset_dict(media_id, **data)
        except Exception as e:
            logger.exception(f"Error adding data `{data}` to redis for id `{media_id}`")
            raise DBError
        logger.info(f"Updated state for `{media_id}` with `{data}`")

    @classmethod
    async def get_state(cls, media_id):
        try:
            return await cls.transport.hgetall(media_id, encoding="utf-8")
        except Exception as e:
            logger.exception(f"Error getting data from redis for id `{media_id}`")
            raise DBError

    @classmethod
    async def delete_state(cls, media_id):
        try:
            return await cls.transport.delete(media_id)
        except Exception as e:
            logger.exception(f"Error deleting data from redis for id `{media_id}`")
            raise DBError

    @classmethod
    async def close(cls):
        await cls.transport.wait_closed()
