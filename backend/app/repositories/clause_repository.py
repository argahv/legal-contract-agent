"""Clause repository — extraction outputs + embedding persistence for pgvector retrieval."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.clause import Clause
from app.repositories.base import BaseRepository


class ClauseRepository(BaseRepository[Clause]):
    model = Clause

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_for_document(self, document_id: UUID) -> list[Clause]:
        stmt = (
            select(Clause)
            .where(Clause.document_id == document_id)
            .order_by(Clause.sequence.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_details(self, clause_id: UUID) -> Clause | None:
        stmt = (
            select(Clause)
            .options(
                selectinload(Clause.risk_assessments),
                selectinload(Clause.redlines),
            )
            .where(Clause.id == clause_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
