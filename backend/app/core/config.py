"""Application configuration — centralized settings with env precedence (12-factor friendly)."""

from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_ROOT.parent


def _env_files() -> tuple[str, ...]:
    """Load repo `.env` first, then optional `backend/.env` overrides — cwd-independent for uvicorn."""
    paths = (_REPO_ROOT / ".env", _BACKEND_ROOT / ".env")
    return tuple(str(p) for p in paths if p.is_file())


class Settings(BaseSettings):
    """Runtime configuration validated at startup; secrets must come from environment only."""

    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_ignore_empty=True,
        extra="ignore",
    )

    app_name: str = "legal-contract-review-api"
    environment: str = Field(default="development", validation_alias="APP_ENV")

    api_v1_prefix: str = "/api/v1"
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated browser origins permitted for credential-bearing requests.",
    )

    jwt_secret_key: str = Field(validation_alias="JWT_SECRET_KEY", min_length=16)
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60,
        validation_alias=AliasChoices("ACCESS_TOKEN_EXPIRE_MINUTES", "JWT_ACCESS_TOKEN_EXPIRE_MINUTES"),
    )
    refresh_token_expire_days: int = Field(
        default=7,
        validation_alias=AliasChoices("REFRESH_TOKEN_EXPIRE_DAYS", "JWT_REFRESH_TOKEN_EXPIRE_DAYS"),
    )

    database_url: str = Field(
        validation_alias="DATABASE_URL",
        description="asyncpg dialect URL, e.g. postgresql+asyncpg://user:pass@host:5432/db",
    )
    sqlalchemy_pool_size: int = Field(default=10)
    sqlalchemy_max_overflow: int = Field(default=20)
    sqlalchemy_pool_timeout_seconds: int = Field(default=30)
    sqlalchemy_pool_recycle_seconds: int = Field(default=1800)

    openai_api_key: str = Field(
        validation_alias=AliasChoices("OPENROUTER_API_KEY", "OPENAI_API_KEY"),
        min_length=1,
        description="OpenRouter or OpenAI key (OpenAI-compatible Chat Completions). OpenRouter listed first so it wins if both env vars are set.",
    )

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def strip_openai_api_key(cls, v: object) -> object:
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError(
                    "OPENROUTER_API_KEY / OPENAI_API_KEY must contain a non-empty secret "
                    "(whitespace-only values are invalid)."
                )
            return stripped
        return v

    openai_api_base: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_BASE_URL", "OPENROUTER_BASE_URL"),
        description="OpenAI-compatible API base. OpenRouter: https://openrouter.ai/api/v1",
    )
    openrouter_http_referer: str | None = Field(
        default=None,
        validation_alias="OPENROUTER_HTTP_REFERER",
        description="Optional site URL sent to OpenRouter (recommended for rankings).",
    )
    openrouter_app_title: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_APP_TITLE", "OPENROUTER_X_TITLE"),
        description="Optional app name sent as X-Title to OpenRouter.",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("OPENROUTER_MODEL", "OPENAI_CHAT_MODEL", "OPENAI_MODEL"),
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("OPENAI_EMBEDDING_MODEL", "OPENROUTER_EMBEDDING_MODEL"),
    )
    llm_temperature: float = Field(default=0.1)
    vector_dim: int = Field(default=1536, validation_alias="VECTOR_DIM")
    openai_request_timeout_seconds: int = Field(default=90, validation_alias="OPENAI_TIMEOUT_SECONDS")
    openai_max_retries: int = Field(default=3, validation_alias="OPENAI_MAX_RETRIES")

    hybrid_playbook_retrieval: bool = Field(
        default=True,
        validation_alias="HYBRID_PLAYBOOK_RETRIEVAL",
        description="Postgres: combine pgvector + full-text (RRF) + lexical rerank.",
    )
    playbook_retrieval_vector_pool: int = Field(default=40, validation_alias="PLAYBOOK_VECTOR_POOL")
    playbook_retrieval_lex_pool: int = Field(default=40, validation_alias="PLAYBOOK_LEX_POOL")
    playbook_retrieval_rrf_k: int = Field(default=60, validation_alias="PLAYBOOK_RRF_K")
    playbook_rerank_top_n: int = Field(default=12, validation_alias="PLAYBOOK_RERANK_TOP_N")

    risk_prompt_version: str = Field(default="v1", validation_alias="RISK_PROMPT_VERSION")
    risk_judgment_cache_enabled: bool = Field(
        default=True,
        validation_alias="RISK_JUDGMENT_CACHE_ENABLED",
    )
    use_langgraph_review: bool = Field(
        default=False,
        validation_alias="USE_LANGGRAPH_REVIEW",
        description="Run ingest→clause phases via LangGraph state machine.",
    )
    risk_use_react: bool = Field(
        default=False,
        validation_alias="RISK_USE_REACT",
        description="Bounded tool-calling loop for playbook search before risk schema output.",
    )

    langchain_tracing_v2: bool = Field(default=False, validation_alias="LANGCHAIN_TRACING_V2")
    langchain_endpoint: str | None = Field(default=None, validation_alias="LANGCHAIN_ENDPOINT")
    langchain_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGCHAIN_API_KEY", "LANGSMITH_API_KEY"),
    )
    langchain_project: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGCHAIN_PROJECT", "LANGSMITH_PROJECT"),
    )

    rate_limit_requests_per_minute: int = Field(default=120, validation_alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=30, validation_alias="RATE_LIMIT_BURST")

    uploads_dir: str = Field(default="/tmp/legal-agent-uploads")
    max_upload_mb: int = Field(default=25, validation_alias="MAX_UPLOAD_MB")
    extracted_text_limit_chars: int = Field(default=200_000)

    google_docai_project_id: str | None = Field(
        default=None,
        validation_alias="GOOGLE_DOCAI_PROJECT_ID",
        description="GCP project id for Document AI (optional — enables cloud OCR when set with processor id).",
    )
    google_docai_location: str = Field(
        default="us",
        validation_alias="GOOGLE_DOCAI_LOCATION",
        description="Document AI processor region, e.g. us, eu.",
    )
    google_docai_processor_id: str | None = Field(
        default=None,
        validation_alias="GOOGLE_DOCAI_PROCESSOR_ID",
        description="Document AI processor id (hex id from console).",
    )

    @model_validator(mode="after")
    def ensure_openai_compatible_base_url(self) -> Self:
        """Default to OpenRouter when unset; every AI call uses a single OpenAI-compatible HTTP base."""

        b = self.openai_api_base
        if b is None or (isinstance(b, str) and not b.strip()):
            object.__setattr__(self, "openai_api_base", "https://openrouter.ai/api/v1")
        else:
            object.__setattr__(self, "openai_api_base", str(b).strip().rstrip("/"))
        return self

    @model_validator(mode="after")
    def normalize_openrouter_model_ids(self) -> Self:
        """OpenRouter lists models as ``provider/model``; bare OpenAI names 404 without the prefix."""

        base = (self.openai_api_base or "").lower()
        if "openrouter.ai" not in base:
            return self

        updates: dict[str, str] = {}

        emb = self.openai_embedding_model.strip()
        if "/" not in emb and emb in {
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002",
        }:
            updates["openai_embedding_model"] = f"openai/{emb}"

        chat = self.openai_model.strip()
        openrouter_bare_chat = {
            "gpt-4o-mini": "openai/gpt-4o-mini",
            "gpt-4o": "openai/gpt-4o",
            "gpt-4-turbo": "openai/gpt-4-turbo",
            "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
        }
        if "/" not in chat and chat in openrouter_bare_chat:
            updates["openai_model"] = openrouter_bare_chat[chat]

        if not updates:
            return self
        for key, value in updates.items():
            object.__setattr__(self, key, value)
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Test helper to reload settings between cases."""
    get_settings.cache_clear()
