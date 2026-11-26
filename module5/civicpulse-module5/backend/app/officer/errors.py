"""Framework-free error types. The API layer converts these to JSON responses
shaped as ``{"detail": {"code": "...", "message": "..."}}``."""


class ServiceError(Exception):
    status_code = 400

    def __init__(self, code: str, message: str, status_code: int | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(ServiceError):
    status_code = 404


class TransitionError(ServiceError):
    status_code = 409


class UploadError(ServiceError):
    status_code = 422


class ValidationFailed(ServiceError):
    status_code = 422
