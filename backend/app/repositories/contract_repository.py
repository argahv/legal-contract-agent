"""Document (contract) repository — ingestion state machine and reviewer visibility scopes."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_for_owner(self, owner_id: UUID, *, limit: int = 50, offset: int = 0) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, *, limit: int = 50, offset: int = 0) -> list[Document]:
        stmt = (
            select(Document)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_clauses(self, document_id: UUID, owner_id: UUID | None = None) -> Document | None:
        stmt = select(Document).options(selectinload(Document.clauses))
        stmt = stmt.where(Document.id == document_id)
        if owner_id is not None:
            stmt = stmt.where(Document.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
