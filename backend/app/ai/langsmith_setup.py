"""LangSmith / LangChain tracing bootstrap — mirrors `.env.example` knobs without hard failures locally."""

from __future__ import annotations

import logging
import os

from app.core.config import Settings


def configure_langsmith(settings: Settings) -> None:
    """Idempotent env wiring so `langchain` picks up tracing without scattering `os.environ` calls."""

    if settings.langchain_api_key:
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.langchain_api_key)
    if settings.langchain_project:
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langchain_project)
    if settings.langchain_endpoint:
        os.environ.setdefault("LANGCHAIN_ENDPOINT", settings.langchain_endpoint)

    tracing = settings.langchain_tracing_v2
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if tracing else "false"
    # Use stdlib logging so this line always routes through `configure_logging()`'s
    # ProcessorFormatter (structlog's BoundLogger + stdlib can misbehave if captured early).
    logging.getLogger(__name__).info(
        "langsmith_config_applied tracing_v2=%s project=%s",
        tracing,
        settings.langchain_project,
    )
