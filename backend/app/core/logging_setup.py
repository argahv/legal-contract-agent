"""Structured logging — emits JSON-ish key/value logs with request/trace correlation."""

from __future__ import annotations

import logging
import sys

import structlog

_logging_configured: bool = False


def configure_logging(json_logs: bool = False) -> None:
    """
    Bind stdlib logging to structlog; JSON mode is preferable in containerized deployments.
    Middleware attaches request_id and trace identifiers per request lifecycle.
    Idempotent: first call wins (including lazy bootstrap from `get_logger()`).
    """
    global _logging_configured
    if _logging_configured:
        return
    _logging_configured = True

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared: list[structlog.types.Processor] = [
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        timestamper,
    ]

    if json_logs:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            *shared,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Return a BoundLogger; configures structlog on first use so modules imported before
    FastAPI `lifespan` still get a working logger (avoids PrintLogger / `extra` crashes).
    """
    if not _logging_configured:
        from app.core.config import get_settings

        settings = get_settings()
        configure_logging(json_logs=settings.environment == "production")
    return structlog.get_logger(name)


def reset_logging_for_tests() -> None:
    """Allow pytest to re-run `configure_logging` after toggling settings."""

    global _logging_configured
    _logging_configured = False
