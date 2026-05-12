"""Risk projections — stable wire shape even when ORM stores JSONB diagnostics."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import RiskLevel


class RiskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clause_id: UUID
    level: RiskLevel
    explanation: str
    rule_hits: list[str] | None = None
    created_at: datetime
