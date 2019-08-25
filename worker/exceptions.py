class WorkerError(Exception):
    pass

class FileError(WorkerError):
    status = 400

class InvalidMedia(WorkerError):
    status = 415

class RawImageError(FileError):
    pass

class ThumbnailImageError(FileError):
    pass

class NotFound(WorkerError):
    status = 422
