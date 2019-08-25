import logging
import aiofiles
from aiofiles.os import os as asynos
from pathlib import Path

from ... exceptions import NotFound

logger = logging.getLogger("aiohttp.client")


class Client:
    input_dir, output_dir = None, None

    @classmethod
    def setup(cls, input_dir, output_dir):
        cls.input_dir = Path(input_dir)
        cls.output_dir = Path(output_dir)

    @classmethod
    async def delete_filedata(cls, filename):
        """
        Given a filename, delete from both input_dir and output_dir
        """
        for data_dir in [cls.input_dir, cls.output_dir]:
            file_location = data_dir / filename
            try:
                await asynos.remove(file_location)
            except Exception as e:
                pass

    @classmethod
    async def save_filedata(cls, filename, data):
        """
        Given filename save file to `input_dir / filename`
        """
        path = cls.input_dir / filename
        async with aiofiles.open(path, mode="wb") as fd:
            await fd.write(data)

    @classmethod
    async def get_filedata(cls, filename):
        """
        Given filename get file from `output_dir / filename`
        """
        path = cls.output_dir / filename
        try:
            async with aiofiles.open(path, mode="rb") as fd:
                return await fd.read()
        except Exception as e:
            raise NotFound(f"file for id and ext `{filename}` not found at {path}")
