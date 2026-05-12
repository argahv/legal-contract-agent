"""Shared config for OpenAI-compatible HTTP APIs (OpenRouter default, OpenAI direct optional).

Chat uses LangChain ``ChatOpenAI``; embeddings use explicit ``httpx`` POSTs so Authorization
cannot be dropped by client edge cases.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings


def _optional_openrouter_headers(settings: Settings) -> dict[str, str] | None:
    headers: dict[str, str] = {}
    if settings.openrouter_http_referer:
        headers["HTTP-Referer"] = settings.openrouter_http_referer
    if settings.openrouter_app_title:
        headers["X-Title"] = settings.openrouter_app_title
    return headers or None


def embeddings_http_headers(settings: Settings) -> dict[str, str]:
    """Headers for ``POST {base}/embeddings`` (and tests)."""

    headers: dict[str, str] = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    optional = _optional_openrouter_headers(settings)
    if optional:
        headers.update(optional)
    return headers


def chat_openai_kwargs(settings: Settings, **overrides: Any) -> dict[str, Any]:
    """Keyword arguments for ``langchain_openai.ChatOpenAI`` (OpenRouter or custom base)."""

    default_headers: dict[str, str] = {
        "Authorization": f"Bearer {settings.openai_api_key}",
    }
    optional = _optional_openrouter_headers(settings)
    if optional:
        default_headers.update(optional)

    kwargs: dict[str, Any] = {
        "api_key": settings.openai_api_key,
        "model": settings.openai_model,
        "temperature": settings.llm_temperature,
        "timeout": settings.openai_request_timeout_seconds,
        "max_retries": 0,
        "openai_api_base": settings.openai_api_base.rstrip("/"),
        "default_headers": default_headers,
    }
    kwargs.update(overrides)
    return kwargs


def create_embeddings_sync(settings: Settings, texts: list[str]) -> list[list[float]]:
    """POST ``/embeddings`` on the configured base URL with explicit Bearer auth (OpenRouter-safe)."""

    base = settings.openai_api_base.rstrip("/")
    url = f"{base}/embeddings"
    headers = embeddings_http_headers(settings)
    payload: dict[str, Any] = {"model": settings.openai_embedding_model, "input": texts}

    with httpx.Client(timeout=settings.openai_request_timeout_seconds) as client:
        response = client.post(url, json=payload, headers=headers)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Embeddings request failed {exc.response.status_code}: {exc.response.text}"
            ) from exc
        body = response.json()

    rows: list[dict[str, Any]] = list(body.get("data") or [])
    if rows and "index" in rows[0]:
        rows = sorted(rows, key=lambda r: int(r["index"]))
    return [list(map(float, row["embedding"])) for row in rows]
