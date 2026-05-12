"""HTTP middleware — request_id propagation and LangSmith/trace-friendly correlation."""

import uuid
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


def correlation_id() -> str:
    """Opaque identifier stitched across logs + downstream AI vendor metadata."""
    return str(uuid.uuid4())


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Binds structured logging context for the lifetime of each HTTP request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-Id") or correlation_id()
        trace_id = request.headers.get("X-Trace-Id") or correlation_id()
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id, trace_id=trace_id)

        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Trace-Id"] = trace_id
        return response
