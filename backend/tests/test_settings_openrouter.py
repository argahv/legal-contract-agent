"""OpenRouter model id normalization on Settings."""

import pytest

from app.core.config import Settings


@pytest.fixture(autouse=True)
def _required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/t")


def test_openrouter_normalizes_bare_openai_embedding_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    s = Settings()
    assert s.openai_embedding_model == "openai/text-embedding-3-small"


def test_openrouter_normalizes_bare_gpt_chat_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    s = Settings()
    assert s.openai_model == "openai/gpt-4o-mini"


def test_plain_openai_base_leaves_models_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")

    s = Settings()
    assert s.openai_embedding_model == "text-embedding-3-small"
    assert s.openai_model == "gpt-4o-mini"


def test_prefixed_ids_pass_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "qwen/qwen3-embedding-8b")
    monkeypatch.setenv("OPENAI_MODEL", "anthropic/claude-3.5-sonnet")

    s = Settings()
    assert s.openai_embedding_model == "qwen/qwen3-embedding-8b"
    assert s.openai_model == "anthropic/claude-3.5-sonnet"
