from .client import Client


async def init_nosql_db(config):
    """
    Configures and returns Cassandra model.
    """
    await Client.setup(config)
    return Client
