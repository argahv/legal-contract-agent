"""FastAPI factory — composes middleware, observability, routers, and websocket ingress."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

import structlog
from fastapi import FastAPI, Request, WebSocket, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure structlog before importing routers/services that might log at import time.
from app.core.config import Settings, get_settings
from app.core.logging_setup import configure_logging, get_logger

_early_settings = get_settings()
configure_logging(json_logs=_early_settings.environment == "production")

from app.ai.langsmith_setup import configure_langsmith
from app.api.deps import decode_access_claims_optional
from app.api.v1 import api_router
from app.api.v1 import health as health_router
from app.core.exceptions import AppError
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import attach_rate_limit_state, limiter
from app.ws.hub import progress_hub

LOG = get_logger(__name__)
_STD_UNHANDLED = logging.getLogger("legal_agent.unhandled_exception")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warms observability + ensures local IO directories exist for dev-readiness."""

    settings = get_settings()
    configure_logging(json_logs=settings.environment == "production")
    configure_langsmith(settings)
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    yield


def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    rid = request.headers.get("X-Request-Id", "")
    settings = get_settings()
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded", "request_id": rid},
        headers=_cors_headers_for_request(request, settings),
    )


def _app_error_handler(request: Request, exc: AppError):
    rid = request.headers.get("X-Request-Id", "")
    ctx = structlog.contextvars.get_contextvars()
    if not rid:
        rid = str(ctx.get("request_id", ""))
    settings = get_settings()
    return JSONResponse(
        status_code=exc.http_status,
        content={"detail": exc.detail, "request_id": rid},
        headers=_cors_headers_for_request(request, settings),
    )


def _cors_headers_for_request(request: Request, settings: Settings) -> dict[str, str]:
    """Mirror CORSMiddleware for responses emitted by ServerErrorMiddleware (outside CORS wrap)."""
    origin = request.headers.get("origin")
    if not origin or origin not in settings.cors_origin_list:
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Vary": "Origin",
    }


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Logged 500 JSON + CORS: Starlette routes Exception handlers through ServerErrorMiddleware (outside CORSMiddleware)."""
    rid = request.headers.get("X-Request-Id", "")
    ctx = structlog.contextvars.get_contextvars()
    if not rid:
        rid = str(ctx.get("request_id", ""))
    settings = get_settings()
    _STD_UNHANDLED.error(
        "unhandled_exception request_id=%s",
        rid,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "request_id": rid},
        headers=_cors_headers_for_request(request, settings),
    )


async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 body validation — same CORS gap as other exception responses (browser hides real error otherwise)."""
    settings = get_settings()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers=_cors_headers_for_request(request, settings),
    )


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Starlette/FastAPI HTTP errors (404, 403, …) — add CORS so the SPA can read JSON on failure."""
    settings = get_settings()
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=_cors_headers_for_request(request, settings),
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "auth", "description": "JWT identity flows."},
            {"name": "contracts", "description": "Contract upload + intelligence reads."},
            {"name": "approvals", "description": "GC approval queue."},
            {"name": "playbook", "description": "Administrative policy corpus."},
            {"name": "audit", "description": "Audit log exports."},
            {"name": "health", "description": "Platform readiness probes."},
        ],
    )

    attach_rate_limit_state(app)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        # Starlette rejects WebSocket upgrades when Origin is not allowed — browsers may send
        # http://127.0.0.1:3000 while CORS_ORIGINS only lists http://localhost:3000.
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)

    app.include_router(health_router.router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.websocket("/ws/contracts/{document_id}/progress")
    async def contract_progress_socket(websocket: WebSocket, document_id: UUID, token: str | None = None):
        await websocket.accept()
        claims = decode_access_claims_optional(token, settings=settings)
        if claims is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
            return
        await progress_hub.register(document_id, websocket)
        try:
            while True:
                await websocket.receive_text()
        finally:
            await progress_hub.unregister(document_id, websocket)

    return app


app = create_app()
