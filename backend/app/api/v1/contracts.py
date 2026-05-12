"""Contract routes — multipart ingress + read models; heavy AI work stays in background workers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from app.api.deps import get_current_user, get_db, settings_dep
from app.core.config import Settings
from app.core.exceptions import ValidationAppError
from app.models.enums import DocumentStatus
from app.models.user import User
from app.repositories.clause_repository import ClauseRepository
from app.schemas.clause import ClauseRead
from app.schemas.contract import ContractRead, ContractStatusRead, ContractUploadResponse
from app.schemas.redline import RedlinePatch, RedlineRead
from app.schemas.risk import RiskRead
from app.services.clause_service import ClauseService
from app.services.contract_service import ContractService
from app.services.redline_service import RedlineService
from app.services.risk_service import RiskService
from app.workers.contract_pipeline import run_contract_pipeline
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

_ALLOWED_MIME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
}


@router.post("/upload", response_model=ContractUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContractUploadResponse:
    payload = await file.read()
    mime = file.content_type or "application/octet-stream"
    if mime not in _ALLOWED_MIME:
        raise ValidationAppError("Unsupported file type")

    service = ContractService(session, settings)
    document = await service.create_from_upload(
        owner_id=current_user.id,
        filename=file.filename or "contract",
        mime_type=mime,
        data=payload,
    )
    await session.commit()
    background_tasks.add_task(run_contract_pipeline, document.id, current_user.id)
    return ContractUploadResponse(
        document_id=document.id,
        status=DocumentStatus(document.status),
    )


@router.get("", response_model=list[ContractRead])
async def list_contracts(
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ContractRead]:
    service = ContractService(session, settings)
    rows = await service.list_accessible(user=current_user)
    return [ContractRead.model_validate(row) for row in rows]


@router.get("/{document_id}", response_model=ContractRead)
async def get_contract(
    document_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContractRead:
    service = ContractService(session, settings)
    document = await service.get_accessible(document_id=document_id, user=current_user)
    return ContractRead.model_validate(document)


@router.get("/{document_id}/status", response_model=ContractStatusRead)
async def contract_status(
    document_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContractStatusRead:
    service = ContractService(session, settings)
    document = await service.get_accessible(document_id=document_id, user=current_user)
    return ContractStatusRead.model_validate(document)


@router.get("/{document_id}/clauses", response_model=list[ClauseRead])
async def list_clauses(
    document_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ClauseRead]:
    service = ClauseService(session)
    rows = await service.list_for_document(document_id=document_id, user=current_user)
    return [ClauseRead.model_validate(row) for row in rows]


@router.get("/{document_id}/risks", response_model=list[RiskRead])
async def list_risks(
    document_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[RiskRead]:
    service = RiskService(session)
    rows = await service.list_for_document(document_id=document_id, user=current_user)
    return [RiskRead.model_validate(row) for row in rows]


@router.get("/{document_id}/redlines", response_model=list[RedlineRead])
async def list_redlines(
    document_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[RedlineRead]:
    service = RedlineService(session)
    clause_lookup = ClauseRepository(session)
    rows = await service.list_for_document(document_id=document_id, user=current_user)
    clauses = {
        clause.id: clause
        for clause in await clause_lookup.list_for_document(document_id)
    }
    redlines: list[RedlineRead] = []
    for row in rows:
        clause = clauses.get(row.clause_id)
        redlines.append(
            RedlineRead.model_validate(row).model_copy(
                update={"original_text": clause.body if clause is not None else None},
            )
        )
    return redlines


@router.patch("/{document_id}/redlines/{redline_id}", response_model=RedlineRead)
async def patch_redline(
    document_id: UUID,
    redline_id: UUID,
    payload: RedlinePatch,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RedlineRead:
    service = RedlineService(session)
    row = await service.update_redline(
        document_id=document_id,
        redline_id=redline_id,
        user=current_user,
        proposed_text=payload.proposed_text,
        status=payload.status,
        reviewer_comment=payload.reviewer_comment,
    )
    clause_lookup = ClauseRepository(session)
    clauses = {
        c.id: c
        for c in await clause_lookup.list_for_document(document_id)
    }
    clause = clauses.get(row.clause_id)
    read = RedlineRead.model_validate(row).model_copy(
        update={"original_text": clause.body if clause is not None else None},
    )
    await session.commit()
    return read


@router.post("/{document_id}/submit-review", response_model=ContractRead)
async def submit_contract_review(
    document_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(settings_dep)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContractRead:
    service = ContractService(session, settings)
    document = await service.submit_for_review(document_id=document_id, user=current_user)
    await session.commit()
    return ContractRead.model_validate(document)
