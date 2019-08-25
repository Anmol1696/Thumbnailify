import logging

from aiohttp import web

from ..utils import raise_json_error
from ...exceptions import BadRequest
from ...models.utils import get_model_from_content_type, get_content_list, object_from_media_id

app_logger = logging.getLogger("aiohttp.application")


class MediaView(web.View):
    async def post(self):
        """
        Handler for receiving media data and store in storage

        202: Accepted - File created, stored, hash pushed to worker queue
        400: BadRequest
        415: UnsupportedMedia
        """
        app = self.request.app
        media_type = self.request.headers.get("Content-Type", None)
        if not media_type:
            raise_json_error(web.HTTPBadRequest, "Missing header Content-Type")

        media_cls = get_model_from_content_type(media_type)
        if not media_cls:
            raise_json_error(
                web.HTTPUnsupportedMediaType, f"Only support Content-Type {get_content_list()}"
            )

        try:
            raw_data = await self.request.text()
        except UnicodeDecodeError as e:
            raise_json_error(web.HTTPBadRequest, e)

        obj = media_cls.from_type_and_data(media_type, raw_data)
        app_logger.info(f"Processed media with id `{obj.filename}`")
        try:
            obj.decode()
        except BadRequest as e:
            raise_json_error(web.HTTPBadRequest, f"Unable to base64 decode. {e}")
        await obj.save(app)
        return web.json_response(obj.db_entry, status=202)


class MediaViewObject(web.View):
    async def get(self):
        obj = await self.get_media_obj()
        status_code = obj.state.pop("code")
        return web.json_response(obj.state, status=status_code)

    async def delete(self):
        obj = await self.get_media_obj()
        await obj.delete(self.request.app)
        return web.HTTPNoContent()

    async def get_media_obj(self):
        media_id = self.request.match_info["id"]
        obj = await object_from_media_id(self.request.app, media_id)
        if not obj:
            raise_json_error(web.HTTPNotFound, f"Resource with id `{media_id}` not found")
        return obj


class MediaViewThumbnailObject(MediaViewObject):
    async def get(self):
        obj = await self.get_media_obj()
        data = await obj.get_thumbnail_data(self.request.app)
        return web.Response(body=data, headers={"Content-Type": obj.media_type})
