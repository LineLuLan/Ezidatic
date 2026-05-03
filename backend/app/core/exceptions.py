"""Application exception hierarchy."""


class AppException(Exception):
    """Base application exception."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class NotFoundError(AppException):
    status_code = 404
    code = "not_found"


class UnauthorizedError(AppException):
    status_code = 401
    code = "unauthorized"


class ValidationError(AppException):
    status_code = 422
    code = "validation_error"


class AllProvidersFailedError(AppException):
    status_code = 503
    code = "llm_unavailable"
