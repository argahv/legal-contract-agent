"""Redline suggestions — union of policy retrieval and generative counsel."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RedlineReviewStatus

if TYPE_CHECKING:
    from app.models.clause import Clause
    from app.models.playbook import PlaybookEntry


class Redline(Base):
    __tablename__ = "redlines"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clause_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clauses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    proposed_text: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=RedlineReviewStatus.PENDING.value,
    )
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    playbook_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("playbook_entries.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    clause: Mapped[Clause] = relationship("Clause", back_populates="redlines")
    playbook_entry: Mapped[PlaybookEntry | None] = relationship("PlaybookEntry", back_populates="redlines")
