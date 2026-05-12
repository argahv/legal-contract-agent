"""Risk assessment repository — append-only scoring trail per clause for audit export."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk import RiskAssessment
from app.repositories.base import BaseRepository


class RiskAssessmentRepository(BaseRepository[RiskAssessment]):
    model = RiskAssessment

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_for_clause(self, clause_id: UUID) -> list[RiskAssessment]:
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.clause_id == clause_id)
            .order_by(RiskAssessment.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
