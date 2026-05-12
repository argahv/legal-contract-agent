"""Audit log repository — append-only ledger queries for compliance exports."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_filtered(
        self,
        *,
        actor_id: UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type is not None:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if created_after is not None:
            stmt = stmt.where(AuditLog.created_at >= created_after)
        if created_before is not None:
            stmt = stmt.where(AuditLog.created_at <= created_before)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
