import importlib
from inspect import isawaitable


async def setup_databases(app):
    config = app["config"]["db"]
    engines = []
    for db_type, db_config in config.items():
        backend = db_config.pop("backend")
        app_key = db_config.pop("app-key", None)
        module_utils = importlib.import_module(f".{backend}.utils", "porta.db")
        engine = await getattr(module_utils, f"init_{db_type}_db")(db_config)
        engines.append(engine)
        if app_key:
            app[app_key] = engine

    async def close_db_engines(app):
        for engine in engines:
            if hasattr(engine, "close"):
                obj = engine.close()
                if isawaitable(obj):
                    await obj

    app.on_cleanup.append(close_db_engines)
