"""Redline DTOs — include optional playbook reference UUID for UI deep-links."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import RedlineReviewStatus, RedlineSource


class RedlineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID
    clause_id: UUID
    source: RedlineSource
    proposed_text: str
    rationale: str
    status: RedlineReviewStatus
    reviewer_comment: str | None = None
    playbook_entry_id: UUID | None
    original_text: str | None = None
    created_at: datetime


class RedlinePatch(BaseModel):
    proposed_text: str | None = Field(default=None, max_length=200_000)
    status: RedlineReviewStatus | None = None
    reviewer_comment: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def require_mutation(self) -> RedlinePatch:
        if self.proposed_text is None and self.status is None and self.reviewer_comment is None:
            raise ValueError("Provide proposed_text, status, and/or reviewer_comment")
        return self
