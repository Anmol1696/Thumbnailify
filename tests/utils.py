import configparser
import base64
from pathlib import Path


def load_config():
    config_data = configparser.ConfigParser(allow_no_value=True)
    config_data.read(Path(__file__).parent.glob("*.ini"))
    return config_data

def file_encoder(filename):
    with open(filename, 'rb') as fd:
        data = fd.read()
    return base64.b64encode(data)
