"""Embeddings use httpx with explicit Authorization (OpenRouter-safe)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.ai.openai_compatible import create_embeddings_sync, embeddings_http_headers
from app.core import config as app_config


@pytest.fixture(autouse=True)
def _required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/t")


def test_embeddings_headers_include_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-integration-test-token")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    app_config.reset_settings_cache()
    from app.core.config import Settings

    s = Settings()
    h = embeddings_http_headers(s)
    assert h["Authorization"] == "Bearer sk-integration-test-token"
    assert h["Content-Type"] == "application/json"
    assert isinstance(h["Authorization"], str)
    assert h["Authorization"] != "Bearer "


@pytest.mark.parametrize(
    "base_url",
    ["https://api.openai.com/v1", "https://openrouter.ai/api/v1", None],
)
def test_create_embeddings_sync_sends_authorization(
    monkeypatch: pytest.MonkeyPatch,
    base_url: str | None,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    if base_url:
        monkeypatch.setenv("OPENROUTER_BASE_URL", base_url)
    app_config.reset_settings_cache()
    from app.core.config import Settings

    s = Settings()
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"data": [{"index": 0, "embedding": [0.1, 0.2]}]}

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            pass

        def __enter__(self) -> FakeClient:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def post(self, url: str, json: dict, headers: dict) -> FakeResponse:
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr("httpx.Client", FakeClient)

    out = create_embeddings_sync(s, ["hello"])
    assert out == [[0.1, 0.2]]
    assert captured["headers"]["Authorization"] == "Bearer sk-or-test"
    assert captured["json"]["model"] == s.openai_embedding_model
    if base_url:
        assert captured["url"] == f"{base_url.rstrip('/')}/embeddings"
    else:
        assert captured["url"] == "https://openrouter.ai/api/v1/embeddings"


def test_whitespace_only_openai_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "   ")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    app_config.reset_settings_cache()
    from app.core.config import Settings

    with pytest.raises(ValidationError):
        Settings()


def test_settings_default_base_is_openrouter_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-x")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    app_config.reset_settings_cache()
    from app.core.config import Settings

    s = Settings()
    assert s.openai_api_base == "https://openrouter.ai/api/v1"
