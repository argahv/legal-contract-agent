"""Playbook admin routes — vectors refresh server-side to prevent client prompt injection."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from app.api.deps import get_db, require_role, settings_dep
from app.core.config import Settings
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.playbook import PlaybookCreate, PlaybookRead, PlaybookUpdate
from app.services.playbook_service import PlaybookService
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=list[PlaybookRead])
async def list_playbook(
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
    _: Annotated[User, Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN))],
) -> list[PlaybookRead]:
    service = PlaybookService(session, settings)
    rows = await service.list_entries()
    return [PlaybookRead.model_validate(row) for row in rows]


@router.post("", response_model=PlaybookRead, status_code=status.HTTP_201_CREATED)
async def create_playbook_entry(
    payload: PlaybookCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
    _: Annotated[User, Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN))],
) -> PlaybookRead:
    service = PlaybookService(session, settings)
    row = await service.create(payload=payload)
    await session.commit()
    return PlaybookRead.model_validate(row)


@router.patch("/{entry_id}", response_model=PlaybookRead)
async def update_playbook_entry(
    entry_id: UUID,
    payload: PlaybookUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
    _: Annotated[User, Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN))],
) -> PlaybookRead:
    service = PlaybookService(session, settings)
    row = await service.update(entry_id=entry_id, payload=payload)
    await session.commit()
    return PlaybookRead.model_validate(row)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_playbook_entry(
    entry_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
    _: Annotated[User, Depends(require_role(UserRole.SUPER_ADMIN, UserRole.ADMIN))],
) -> Response:
    service = PlaybookService(session, settings)
    await service.delete(entry_id=entry_id)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
