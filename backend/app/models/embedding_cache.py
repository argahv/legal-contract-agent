"""Embedding cache rows — persistence tier for sha256-keyed embedding lookups across workers."""

from __future__ import annotations

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmbeddingCache(Base):
    """Stores embedding vectors as JSON lists to stay portable for SQLite-backed unit tests."""

    __tablename__ = "embedding_cache"

    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    model_name: Mapped[str] = mapped_column(String(128), primary_key=True)
    dims: Mapped[int] = mapped_column(Integer, nullable=False)
    vector: Mapped[list[float]] = mapped_column(JSON, nullable=False)
