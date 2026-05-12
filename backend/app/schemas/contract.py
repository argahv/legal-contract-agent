"""Contract DTOs — separate upload response from fully hydrated reads for pagination budgets."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.enums import DocumentStatus


class ContractUploadResponse(BaseModel):
    document_id: UUID
    status: DocumentStatus
    message: str = "upload_accepted"


class ContractStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: DocumentStatus
    progress_percent: int = Field(ge=0, le=100)
    failure_reason: str | None = None


class ContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    owner_id: UUID
    filename: str
    mime_type: str | None
    status: DocumentStatus
    progress_percent: int
    failure_reason: str | None
    submitted_for_review_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    content: str | None = Field(
        default=None,
        validation_alias=AliasChoices("extracted_text", "content"),
    )
