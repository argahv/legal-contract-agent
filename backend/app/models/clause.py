"""Clause entity — atomic contract unit produced by structured extraction chain."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EMBEDDING_DIMENSIONS
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.approval import Approval
    from app.models.document import Document
    from app.models.redline import Redline
    from app.models.risk import RiskAssessment


class Clause(Base):
    __tablename__ = "clauses"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clause_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship("Document", back_populates="clauses")
    risk_assessments: Mapped[list[RiskAssessment]] = relationship(
        "RiskAssessment",
        back_populates="clause",
        cascade="all, delete-orphan",
    )
    redlines: Mapped[list[Redline]] = relationship(
        "Redline",
        back_populates="clause",
        cascade="all, delete-orphan",
    )
    approvals: Mapped[list[Approval]] = relationship(
        "Approval",
        back_populates="clause",
        cascade="all, delete-orphan",
    )
