"""Consistent Error Handling and Exception Schemas for ToolNest."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorResponse(BaseModel):
    """Standardized API Error Response schema."""

    code: str
    message: str


class ToolNestError(Exception):
    """Base application exception for ToolNest with error code and status."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.headers = headers or {}
        super().__init__(message)


class FileTooLargeError(ToolNestError):
    def __init__(
        self,
        message: str = "This file is larger than the limit shown on this page. Try a smaller file",
    ) -> None:
        super().__init__(
            code="FILE_TOO_LARGE",
            message=message,
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
        )


class UnsupportedTypeError(ToolNestError):
    def __init__(
        self,
        message: str = "This tool accepts supported file formats only",
    ) -> None:
        super().__init__(
            code="UNSUPPORTED_TYPE",
            message=message,
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )


class CorruptFileError(ToolNestError):
    def __init__(
        self,
        message: str = "We could not read this file. Check that it opens on your device",
    ) -> None:
        super().__init__(
            code="CORRUPT_FILE",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )


class PasswordProtectedError(ToolNestError):
    def __init__(
        self,
        message: str = "This PDF is password protected. Remove the password and try again",
    ) -> None:
        super().__init__(
            code="PASSWORD_PROTECTED",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )


class TooManyFilesError(ToolNestError):
    def __init__(
        self,
        message: str = "You can upload up to 5 files at a time",
    ) -> None:
        super().__init__(
            code="TOO_MANY_FILES",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class PageLimitError(ToolNestError):
    def __init__(
        self,
        message: str = "This PDF has more pages than this tool supports",
    ) -> None:
        super().__init__(
            code="PAGE_LIMIT",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )


class DailyLimitError(ToolNestError):
    def __init__(
        self,
        message: str = "You have reached today's free limit. It resets at midnight IST",
    ) -> None:
        super().__init__(
            code="DAILY_LIMIT",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class RateLimitedError(ToolNestError):
    def __init__(
        self,
        message: str = "Too many requests. Please wait a minute",
    ) -> None:
        super().__init__(
            code="RATE_LIMITED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class ServerBusyError(ToolNestError):
    def __init__(
        self,
        message: str = "The tool is busy right now. Please try again in a moment",
    ) -> None:
        super().__init__(
            code="SERVER_BUSY",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={"Retry-After": "10"},
        )


class TimeoutError(ToolNestError):
    def __init__(
        self,
        message: str = "This file took too long to process. Try a smaller file",
    ) -> None:
        super().__init__(
            code="TIMEOUT",
            message=message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )


class ServerError(ToolNestError):
    def __init__(
        self,
        message: str = "Something went wrong on our side. Please try again",
    ) -> None:
        super().__init__(
            code="SERVER_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def register_error_handlers(app: FastAPI) -> None:
    """Register custom exception handlers that guarantee uniform JSON error contracts."""

    @app.exception_handler(ToolNestError)
    async def toolnest_exception_handler(_: Request, exc: ToolNestError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Map common HTTP status codes to defined PRD error codes
        code_map = {
            400: "TOO_MANY_FILES" if "file" in str(exc.detail).lower() else "INVALID_REQUEST",
            404: "NOT_FOUND",
            413: "FILE_TOO_LARGE",
            415: "UNSUPPORTED_TYPE",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMITED",
            503: "SERVER_BUSY",
            504: "TIMEOUT",
            500: "SERVER_ERROR",
        }
        code = code_map.get(exc.status_code, "SERVER_ERROR")
        detail = str(exc.detail) if exc.detail else "An unexpected error occurred."
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": code, "message": detail},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Provide a sanitized clean message without leaking internal details
        first_error = exc.errors()[0] if exc.errors() else {}
        field = " -> ".join(str(loc) for loc in first_error.get("loc", []))
        msg = first_error.get("msg", "Invalid request parameters")
        detail = f"Invalid input for {field}: {msg}" if field else msg
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"code": "VALIDATION_ERROR", "message": detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        # Catch unexpected errors, log safely without exposing traceback to client
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "SERVER_ERROR",
                "message": "Something went wrong on our side. Please try again",
            },
        )
