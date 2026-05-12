"""Approval routes — GC queue operations with explicit decision audit trail."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from app.api.deps import get_db, require_role
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.approval import ApprovalDecision, ApprovalRead
from app.services.approval_service import ApprovalService
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/pending", response_model=list[ApprovalRead])
async def list_pending(
    session: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[
        User,
        Depends(
            require_role(
                UserRole.SUPER_ADMIN,
                UserRole.ADMIN,
                UserRole.GENERAL_COUNSEL,
            ),
        ),
    ],
) -> list[ApprovalRead]:
    service = ApprovalService(session)
    return await service.list_pending(actor_role=UserRole(actor.role))


@router.post("/{approval_id}/decision", response_model=ApprovalRead)
async def decide(
    approval_id: UUID,
    payload: ApprovalDecision,
    session: Annotated[AsyncSession, Depends(get_db)],
    actor: Annotated[
        User,
        Depends(
            require_role(
                UserRole.SUPER_ADMIN,
                UserRole.ADMIN,
                UserRole.GENERAL_COUNSEL,
            ),
        ),
    ],
) -> ApprovalRead:
    service = ApprovalService(session)
    approval = await service.decide(
        approval_id=approval_id,
        payload=payload,
        reviewer_id=actor.id,
        actor_role=UserRole(actor.role),
    )
    await session.commit()
    return ApprovalRead.model_validate(approval)
