"""Domain / HTTP exception vocabulary — centralized mapping keeps routers thin."""

from fastapi import HTTPException, status


class AppError(Exception):
    """Non-HTTP semantic error raised from services/repos; handlers translate."""

    http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    http_status = status.HTTP_404_NOT_FOUND


class UnauthorizedError(AppError):
    http_status = status.HTTP_401_UNAUTHORIZED


class ForbiddenError(AppError):
    http_status = status.HTTP_403_FORBIDDEN


class ConflictError(AppError):
    http_status = status.HTTP_409_CONFLICT


class ValidationAppError(AppError):
    http_status = status.HTTP_422_UNPROCESSABLE_ENTITY


class BadRequestError(AppError):
    http_status = status.HTTP_400_BAD_REQUEST


class ExternalServiceError(AppError):
    """Upstream vendor failure (OpenAI, OCR, etc.) — mapped to 502."""

    http_status = status.HTTP_502_BAD_GATEWAY


class ServiceUnavailableError(AppError):
    """Overload / vendor outage — mapped to 503 with Retry-After hooks at edge."""

    http_status = status.HTTP_503_SERVICE_UNAVAILABLE


class RateLimitAppError(AppError):
    """Domain-level rate limit (distinct from slowapi HTTP 429 on edge)."""

    http_status = status.HTTP_429_TOO_MANY_REQUESTS


def to_http(exc: Exception) -> HTTPException:
    if isinstance(exc, AppError):
        return HTTPException(status_code=exc.http_status, detail=exc.detail)
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
