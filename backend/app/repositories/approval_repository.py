"""Approval repository — dual-control queue for HIGH/CRITICAL risk escalations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.approval import Approval
from app.models.enums import ApprovalScope, ApprovalStatus
from app.repositories.base import BaseRepository


class ApprovalRepository(BaseRepository[Approval]):
    model = Approval

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_pending_for_counsel(self, *, limit: int = 100, offset: int = 0) -> list[Approval]:
        stmt = (
            select(Approval)
            .options(
                selectinload(Approval.document),
                selectinload(Approval.requested_by),
            )
            .where(Approval.status == ApprovalStatus.PENDING.value)
            .order_by(Approval.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def has_pending_document_approval(self, document_id: UUID) -> bool:
        stmt = (
            select(Approval.id)
            .where(
                Approval.document_id == document_id,
                Approval.status == ApprovalStatus.PENDING.value,
                Approval.scope == ApprovalScope.DOCUMENT.value,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_for_document(self, document_id: UUID) -> list[Approval]:
        stmt = select(Approval).where(Approval.document_id == document_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_document(self, approval_id: UUID, document_id: UUID) -> Approval | None:
        stmt = select(Approval).where(Approval.id == approval_id, Approval.document_id == document_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
