import os
import yaml
import logging
from pathlib import Path

from .db import setup_db

CONFIG_PATH = Path(__file__).parent.parent / "config"


def env_constructor(loader, node):
    fields = loader.construct_scalar(node)
    env, *default = fields.split(" ")
    value = os.environ.get("THUMBNAILIFY_%s" % env.upper(), " ".join(default))
    return int(value) if value.isdigit() else value


yaml.add_constructor("!env", env_constructor)


def init_config(config_file="worker.yaml"):
    with open(CONFIG_PATH / config_file) as rf:
        config = yaml.load(rf, Loader=yaml.Loader)
    return config


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


config = init_config()
setup_logging()
setup_db(config["db"])
