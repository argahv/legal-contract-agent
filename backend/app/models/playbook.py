"""Enterprise playbook embeddings — similarity retrieval drives consistent redlines."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EMBEDDING_DIMENSIONS
from app.db.base import Base

# re-export for consumers that imported from playbook historically
__all__ = ["PlaybookEntry", "EMBEDDING_DIMENSIONS"]

if TYPE_CHECKING:
    from app.models.redline import Redline


class PlaybookEntry(Base):
    __tablename__ = "playbook_entries"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    clause_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    guideline: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_language: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    redlines: Mapped[list[Redline]] = relationship("Redline", back_populates="playbook_entry")
