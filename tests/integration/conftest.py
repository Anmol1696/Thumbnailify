import io
import configparser
import base64
from pathlib import Path

import pytest
import requests
from wand.image import Image

from ..utils import load_config, file_encoder


@pytest.fixture(scope="session")
def config_data():
    return load_config()


@pytest.fixture
def image_encoder(config_data):
    base_dir = Path(config_data["data"]["dir"])

    return lambda x: file_encoder(base_dir / x)


@pytest.fixture
def verify_image():
    def factory(encoded_image, max_width=100, max_height=100):
        decode = base64.b64decode(encoded_image)
        with Image(file=io.BytesIO(decode)) as img:
            return img.width <= max_width and img.height <= max_height

    return factory


@pytest.fixture
def make_requests(config_data):
    endpoint_map = config_data["server-endpoint"]
    def factory(endpoint, method, data=None, **kwargs):
        action = getattr(requests, method)
        url = endpoint_map.get(endpoint)
        resp = action(url, data=data, headers=kwargs)
        return resp
    return factory
