"""Clause + intelligence DTOs — extraction confidence surfaces reviewer trust in UI."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ClauseType


class ClauseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    sequence: int
    clause_type: ClauseType
    title: str | None
    body: str
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime
