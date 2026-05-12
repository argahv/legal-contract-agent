"""Audit service — centralizes payload redaction policies before persistence."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_setup import get_logger
from app.models.audit import AuditLog
from app.models.enums import AuditAction
from app.repositories.audit_repository import AuditLogRepository

LOG = get_logger(__name__)


class AuditService:
    """Facades repository writes so routers never construct ORM rows directly."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AuditLogRepository(session)

    async def record(
        self,
        *,
        actor_id: UUID | None,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        payload: Mapping[str, object] | None = None,
    ) -> AuditLog:
        row = AuditLog(
            actor_id=actor_id,
            action=action.value,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=dict(payload) if payload is not None else None,
        )
        LOG.info("audit_record", action=action.value, entity_type=entity_type, entity_id=entity_id)
        return await self.repo.add(row)
