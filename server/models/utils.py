import uuid

from . import media

CONTENT_LIST = [
    "image",
]
DB_ENGINE = "redis"


def get_random_uuid():
    return str(uuid.uuid4())

def get_content_list():
    return CONTENT_LIST


def get_model_from_content_type(media_type):
    if media_type.split("/")[0] in CONTENT_LIST:
        return media.Media
    return None


async def object_from_media_id(app, media_id):
    state = await app[DB_ENGINE].get_state(media_id)
    if not state:
        return None
    mcls = get_model_from_content_type(state.get("media_type"))
    return mcls(media_id=media_id, **state)
