"""Playbook admin DTOs — embedding is never accepted from clients; computed server-side."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ClauseType


class PlaybookCreate(BaseModel):
    title: str = Field(min_length=3, max_length=256)
    clause_type: ClauseType
    guideline: str = Field(min_length=10)
    preferred_language: str | None = Field(default=None, max_length=20_000)


class PlaybookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=256)
    clause_type: ClauseType | None = None
    guideline: str | None = Field(default=None, min_length=10)
    preferred_language: str | None = Field(default=None, max_length=20_000)


class PlaybookRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    clause_type: ClauseType
    guideline: str
    preferred_language: str | None
    created_at: datetime
