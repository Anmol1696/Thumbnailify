import importlib
import logging
import logging.config
import os
import typing
from collections import defaultdict
from pathlib import Path

import yaml

CONFIG_KEY = "config"
CONFIG_PATH = Path(__file__).parent.parent / CONFIG_KEY
CONSOLE_LOG_ENVIRONMENTS = ["local"]


def env_constructor(loader, node):
    """
    Return the system environment variable env if it exists,
    otherwise return the given default environment
    """
    fields = loader.construct_scalar(node)
    env, *default = fields.split(" ")
    value = os.environ.get("PORTA_%s" % env.upper(), " ".join(default))
    return int(value) if value.isdigit() else value


yaml.add_constructor("!env", env_constructor)


def init_config(app, config_file="server.yaml"):
    with open(CONFIG_PATH / config_file) as rf:
        app[CONFIG_KEY] = yaml.load(rf)
    features = app[CONFIG_KEY]["features"] or {}
    env_features = os.environ.get("PORTA_FEATURES")
    if env_features:
        features.update(dict.fromkeys(env_features.split(","), True))
    app.feature = DefaultObjectDict(bool, features)
    env_versions = os.environ.get("PORTA_VERSIONS")
    if env_versions:
        versions = env_versions.split(",")
    else:
        versions = app[CONFIG_KEY]["versions"]
    app.versions = [v.split(".")[0] for v in versions]


def init_logging(app):
    config = app[CONFIG_KEY]["logging"]
    log_dir = Path(config["dir"])
    handlers = {}
    loggers = {}
    config_dict = dict(config[CONFIG_KEY], handlers=handlers, loggers=loggers)
    handler_defaults = config["handler_defaults"]
    for logger in config["loggers"]:
        fname = logger.split(".")[-1]
        handler_name = f"aiohttp_{fname}_handler"
        handler_dict = dict(filename=log_dir / f"{fname}.log", **handler_defaults)
        if fname == "access":
            handler_dict["formatter"] = "brief"
        handlers[handler_name] = handler_dict
        loggers[logger] = {"handlers": [handler_name]}
    root_logger = logging.getLogger()
    log_level = getattr(logging, config["level"].upper())
    root_logger.setLevel(log_level)
    if app[CONFIG_KEY]["server"]["environment"] in CONSOLE_LOG_ENVIRONMENTS:
        root_logger.addHandler(logging.StreamHandler())
    logging.config.dictConfig(config_dict)


def setup_routes(app):
    for module_name in app["config"]["modules"]:
        module_routes = importlib.import_module(f".{module_name}.routes", "porta")
        module_routes.setup_routes(app)


class ObjectDict(typing.Dict[str, typing.Any]):
    """
    Makes a dictionary behave like an object, with attribute-style access.

    Note: copied from Tornado's util module.
    """

    def __getattr__(self, name):
        # type: (str) -> Any
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        # type: (str, Any) -> None
        self[name] = value


class DefaultObjectDict(defaultdict, ObjectDict):
    pass
