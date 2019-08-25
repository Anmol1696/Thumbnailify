import logging

from pathlib import Path

from ...exceptions import DBIntegrityError
from .client import Client

logger = logging.getLogger("aiohttp.server")


def setup_files(config):
    dir_path = Path(config.get("dir", "."))
    if not dir_path.is_dir():
        logger.error(f"Volume path `{dir_path.absolute()}` is not dir")
        raise DBIntegrityError
    input_dir = dir_path / config.get("input-dir", "raw")
    output_dir = dir_path / config.get("output-dir", "completed")
    try:
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.error(
            f"Permission Denied for setting up `{input_dir.absolute()}` "
            "and `{output_dir.absolute()}`"
        )
        raise DBIntegrityError
    logger.info(f"Folders `{input_dir.absolute()}` and `{output_dir.absolute()}` setup complete")
    return input_dir.absolute(), output_dir.absolute()


async def init_file_db(config):
    input_dir, output_dir = setup_files(config)
    Client.setup(input_dir, output_dir)
    return Client
