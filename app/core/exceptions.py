import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


class AppError(Exception):
    """Base class for application-specific errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class InvalidTokenError(AppError):
    def __init__(self, message: str = "Invalid or expired token."):
        super().__init__(message, status_code=400)


class TokenExpiredError(AppError):
    def __init__(self, message: str = "This magic link has expired."):
        super().__init__(message, status_code=400)


class TokenAlreadyUsedError(AppError):
    def __init__(self, message: str = "This magic link has already been used."):
        super().__init__(message, status_code=400)


class UserNotFoundError(AppError):
    def __init__(self, message: str = "User not found."):
        super().__init__(message, status_code=404)


class NotAuthenticatedError(AppError):
    def __init__(self, message: str = "Could not validate credentials."):
        super().__init__(message, status_code=401)


def register_exception_handlers(app: FastAPI) -> None:
    """Turn any AppError into {"detail": message} with its status code; catch-all 500 otherwise."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        log = logger.warning if exc.status_code < 500 else logger.error
        log(
            "Request failed with an application error.",
            message=exc.message,
            status_code=exc.status_code,
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Request failed with an unhandled exception.")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
