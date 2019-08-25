import redis
import logging


class Client:
    redis_client = None

    @classmethod
    def setup(cls, config):
        cls.redis_client = redis.Redis(**config)

    @classmethod
    def close(cls):
        cls.redis_client.close()

    @classmethod
    def update_state(cls, media_id, **data):
        cls.redis_client.hmset(media_id, data)
        logging.info(f"Updated state for `{media_id}` with `{data}`")

    @classmethod
    def get_state(cls, media_id):
        cls.redis_client.hgetall(media_id)


def setup_db(config):
    Client.setup(config)
