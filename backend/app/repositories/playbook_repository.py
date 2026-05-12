"""Playbook repository — admin CRUD plus vector-friendly bulk fetch for seed jobs."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.playbook import PlaybookEntry
from app.repositories.base import BaseRepository


class PlaybookRepository(BaseRepository[PlaybookEntry]):
    model = PlaybookEntry

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_by_clause_type(self, clause_type: str) -> list[PlaybookEntry]:
        stmt = select(PlaybookEntry).where(PlaybookEntry.clause_type == clause_type)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all_entries(self, *, limit: int = 500, offset: int = 0) -> list[PlaybookEntry]:
        stmt = select(PlaybookEntry).order_by(PlaybookEntry.created_at.asc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
