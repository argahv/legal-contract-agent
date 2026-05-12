"""Redline repository — playbook-linked suggestions materialized for reviewer UX."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.redline import Redline
from app.repositories.base import BaseRepository


class RedlineRepository(BaseRepository[Redline]):
    model = Redline

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_for_document_via_clauses(self, document_id: UUID) -> list[Redline]:
        from app.models.clause import Clause

        stmt = (
            select(Redline)
            .join(Clause, Redline.clause_id == Clause.id)
            .where(Clause.document_id == document_id)
            .options(joinedload(Redline.playbook_entry))
            .order_by(Redline.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_by_id_for_document(self, redline_id: UUID, document_id: UUID) -> Redline | None:
        from app.models.clause import Clause

        stmt = (
            select(Redline)
            .join(Clause, Redline.clause_id == Clause.id)
            .where(Redline.id == redline_id, Clause.document_id == document_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
