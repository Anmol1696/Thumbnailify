import asyncio

from aiohttp import web

from .db.utils import setup_databases
from .utils import init_config, init_logging, setup_routes


async def init():
    app = web.Application()
    init_config(app)
    init_logging(app)
    await setup_databases(app)
    setup_routes(app)
    return app


def main():
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init())
    web.run_app(
        app,
        host=app["config"]["server"]["host"],
        port=app["config"]["server"]["port"],
        access_log_format=app["config"]["logging"]["access-format"],
    )


if __name__ == "__main__":
    main()
