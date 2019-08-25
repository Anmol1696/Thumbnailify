import uuid
import base64

from ..exceptions import BadRequest, DBIntegrityError

MEDIA_STORAGE_ENGINE = "filesystem"
QUEUE_ENGINE = "queue"
DB_ENGINE = "redis"


class Media:
    def __init__(self, **kwargs):
        self.id = kwargs["media_id"]
        self.media_type = kwargs["media_type"]
        self.content, self.ext = self.media_type.split("/")
        self.raw_data = kwargs.get("raw_data", None)
        self.state = kwargs

    @property
    def filename(self):
        return f"{self.id}.{self.ext}"

    @property
    def db_entry(self):
        return {
            "media_id": self.id,
            "media_type": self.media_type,
            "message": f"Processing {self.content}, use `media_id` to check status",
            "service": "webserver",
            "state": "Processing",
        }

    def decode(self):
        try:
            self.data = base64.b64decode(self.raw_data)
        except base64.binascii.Error:
            raise BadRequest("Invalid base64-encoded image body")
        except UnicodeDecodeError as e:
            raise BadRequest(f"Unable to base64 decode. {e}")

    def encode(self):
        try:
            self.data = base64.b64encode(self.raw_data)
        except base64.binascii.Error:
            raise DBIntegrityError(f"")

    async def save(self, app):
        """
        Save object to filesystem, send to queue, send data to db
        """
        await app[MEDIA_STORAGE_ENGINE].save_filedata(f"{self.filename}", self.data)
        await app[QUEUE_ENGINE].add_task(self.id, media_type=self.media_type)
        await app[DB_ENGINE].update_state(code=102, **self.db_entry)

    async def delete(self, app):
        await app[DB_ENGINE].delete_state(self.id)
        await app[MEDIA_STORAGE_ENGINE].delete_filedata(self.filename)

    async def get_thumbnail_data(self, app):
        data = await app[MEDIA_STORAGE_ENGINE].get_filedata(self.filename)
        return base64.b64encode(data)

    @classmethod
    def from_type_and_data(cls, media_type, raw_data):
        return cls(media_id=str(uuid.uuid4()), media_type=media_type, raw_data=raw_data)
