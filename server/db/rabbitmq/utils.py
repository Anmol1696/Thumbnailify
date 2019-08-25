from .client import Client


async def init_queue_db(config):
    await Client.setup(config)
    return Client
