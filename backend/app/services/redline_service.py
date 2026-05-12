"""Redline aggregation — returns ORM rows; API layer hydrates original text for clients."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access import can_access_owned_document
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.enums import AuditAction, RedlineReviewStatus
from app.models.redline import Redline
from app.models.user import User
from app.repositories.contract_repository import DocumentRepository
from app.repositories.redline_repository import RedlineRepository
from app.services.audit_service import AuditService


class RedlineService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._redlines = RedlineRepository(session)
        self._documents = DocumentRepository(session)
        self._audit = AuditService(session)

    async def list_for_document(self, *, document_id: UUID, user: User) -> list[Redline]:
        document = await self._documents.get_by_id(document_id)
        if document is None or not can_access_owned_document(document_owner_id=document.owner_id, user=user):
            raise ForbiddenError("Not allowed to view redlines for this document")
        return await self._redlines.list_for_document_via_clauses(document_id)

    async def update_redline(
        self,
        *,
        document_id: UUID,
        redline_id: UUID,
        user: User,
        proposed_text: str | None,
        status: RedlineReviewStatus | None,
        reviewer_comment: str | None,
    ) -> Redline:
        document = await self._documents.get_by_id(document_id)
        if document is None or not can_access_owned_document(document_owner_id=document.owner_id, user=user):
            raise ForbiddenError("Not allowed to update redlines for this document")

        row = await self._redlines.get_by_id_for_document(redline_id, document_id)
        if row is None:
            raise NotFoundError("Redline not found")

        if proposed_text is not None:
            cleaned = proposed_text.strip()
            if len(cleaned) == 0:
                raise ValidationAppError("proposed_text cannot be empty")
            row.proposed_text = cleaned
        if status is not None:
            row.status = status.value
        if reviewer_comment is not None:
            row.reviewer_comment = reviewer_comment.strip() or None

        await self._session.flush()
        await self._audit.record(
            actor_id=user.id,
            action=AuditAction.REDLINE_UPDATED,
            entity_type="redline",
            entity_id=str(row.id),
            payload={
                "document_id": str(document_id),
                "clause_id": str(row.clause_id),
                "status": row.status,
                "updated_proposed": proposed_text is not None,
            },
        )
        return row
