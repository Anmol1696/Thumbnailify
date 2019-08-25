from aiohttp import web


class ThumbBaseException(Exception):
    status = None


class BadRequest(ThumbBaseException):
    status = 400


class Unauthorized(ThumbBaseException):
    status = 401


class NotFound(ThumbBaseException):
    status = 404


class ServiceUnavailable(ThumbBaseException):
    status = 503


class DBError(ThumbBaseException):
    status = 500


class DBRunTimeError(DBError):
    pass


class DBIntegrityError(DBError):
    pass
