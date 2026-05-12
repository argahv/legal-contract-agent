"""Approval workflow DTOs — GC decisions are explicit to keep audit trail machine-parseable."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ApprovalScope, ApprovalStatus


class ApprovalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scope: ApprovalScope
    status: ApprovalStatus
    document_id: UUID
    clause_id: UUID | None
    requested_by_id: UUID | None
    reviewer_id: UUID | None
    notes: str | None
    created_at: datetime
    decided_at: datetime | None
    # Populated by list/detail handlers (not ORM columns); used by API clients.
    document_filename: str | None = None
    document_status: str | None = None
    document_uploaded_at: datetime | None = None
    requested_by_email: str | None = None


class ApprovalDecision(BaseModel):
    decision: ApprovalStatus
    comment: str | None = Field(default=None, max_length=4000)
