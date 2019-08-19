import logging

from aiohttp import web

import base64
from hashlib import md5

from ..utils import raise_json_error

MEDIA_STORAGE_ENGINE = "storage"
QUEUE_ENGINE = "queue"
app_logger = logging.getLogger("aiohttp.application")

MEDIA_CONTENT = ["image"]

async def media_handler(request):
    """
    Handler for receiving media data and store in storage

    200: OK - File created, stored, hash pushed to worker queue
    400: BadRequest
    415: UnsupportedMedia
    """
    media_type = request.headers.get("Content-Type", None)
    if not media_type:
        raise_json_error(web.HTTPBadRequest, "Missing header Content-Type")
    media_content, media_ext = media_type.split("/")
    if media_content not in MEDIA_CONTENT:
        raise_json_error(web.HTTPUnsupportedMediaType, f"Only support for {MEDIA_CONTENT}")
    raw_media_data = async request.text()

    media_id = md5(raw_media_data)
    media_data = base64.b64decode(raw_media_data)

    with aiofiles.open(f"{media_id}.{media_ext}", 'rb') as fd:
        fd.write(media_data)

    return web.json_response(
        {
            "message": f"Processing {media_content}, use `media_id` to check status",
            "media_id": media_id,
            "status": "In Queue"
        }
    )
