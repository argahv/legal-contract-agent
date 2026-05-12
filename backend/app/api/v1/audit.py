"""Audit routes — read-only exports for SIEM forwarding (filters map to repository query)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from app.api.deps import get_db, require_role
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.audit import AuditLogRead
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=list[AuditLogRead])
async def list_audit_logs(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(
            require_role(
                UserRole.SUPER_ADMIN,
                UserRole.ADMIN,
                UserRole.GENERAL_COUNSEL,
            ),
        ),
    ],
    actor_id: UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
) -> list[AuditLogRead]:
    repo = AuditLogRepository(session)
    rows = await repo.list_filtered(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset,
    )
    return [AuditLogRead.model_validate(row) for row in rows]
