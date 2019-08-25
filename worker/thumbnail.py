from pathlib import Path
from wand.image import Image
from wand.exceptions import CorruptImageError

from .utils import config
from .exceptions import InvalidMedia, RawImageError, NotFound

storage_config = config.get("file_storage", {})


class ThumbHandler:
    # Supported media types
    MEDIA_TYPES = ["image"]

    # Default file storage
    DEFAULT_DIR = "/tmp/thumbnailify"
    DEFAULT_INPUT_DIR = "raw"
    DEFAULT_OUTPUT_DIR = "completed"

    def __init__(self):
        self._handlers = {}
        self.register_custom_handlers()
        self.input_folder, self.output_folder = self.initialize_storage()

    def __call__(self, **kwargs):
        self.handler(**kwargs)

    def initialize_storage(self):
        file_dir = Path(storage_config.get("dir", self.DEFAULT_DIR))
        input_folder = file_dir / storage_config.get("input", self.DEFAULT_INPUT_DIR)
        output_folder = file_dir / storage_config.get("output", self.DEFAULT_OUTPUT_DIR)
        # Create Dir if not exists
        input_folder.mkdir(parents=True, exist_ok=True)
        output_folder.mkdir(parents=True, exist_ok=True)
        return input_folder, output_folder

    def register_custom_handlers(self):
        [self.register(media_type, getattr(self, media_type)) for media_type in self.MEDIA_TYPES]

    def register(self, key, handler):
        self._handlers[key] = handler

    def handler(self, **kwargs):
        key = kwargs["media_type"].split("/")[0]
        handler = self._handlers.get(key, self.default)
        return handler(**kwargs)

    def image(self, media_type, media_id, size="100x100"):
        ext = media_type.split("/")[1]
        input_file = (self.input_folder / f"{media_id}.{ext}").resolve()
        if not input_file.is_file():
            raise NotFound(f"File not found `{input_file}`, file should be present")
        output_file = (self.output_folder / f"{media_id}.{ext}").resolve()
        try:
            with Image(filename=str(input_file)) as img:
                img.transform(resize=size)
                img.save(filename=str(output_file))
        except CorruptImageError as e:
            raise RawImageError(f"Corroupted raw image, please try again")
        else:
            input_file.unlink()

    def default(self, media_type, **kwargs):
        raise InvalidMedia(f"Media type {media_id} not supported, yet!!")


thumbnailify = ThumbHandler()
