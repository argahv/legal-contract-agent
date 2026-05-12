"""Contract lifecycle — owns filesystem persistence + status transitions."""

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access import user_has_full_tenant_access
from app.core.config import Settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.document import Document
from app.models.enums import AuditAction, DocumentStatus
from app.models.user import User
from app.repositories.contract_repository import DocumentRepository
from app.services.audit_service import AuditService


class ContractService:
    """Coordinates durable storage paths with transactional document rows."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._documents = DocumentRepository(session)
        self._audit = AuditService(session)

    def _ensure_upload_dir(self) -> Path:
        target = Path(self._settings.uploads_dir)
        target.mkdir(parents=True, exist_ok=True)
        return target

    async def create_from_upload(
        self,
        *,
        owner_id: UUID,
        filename: str,
        mime_type: str | None,
        data: bytes,
    ) -> Document:
        max_bytes = self._settings.max_upload_mb * 1024 * 1024
        if len(data) > max_bytes:
            raise ValidationAppError("File exceeds configured MAX_UPLOAD_MB")

        upload_root = self._ensure_upload_dir()
        suffix = Path(filename).suffix
        storage_name = f"{uuid4()}{suffix}"
        storage_path = upload_root / storage_name
        storage_path.write_bytes(data)

        document = Document(
            owner_id=owner_id,
            filename=filename,
            mime_type=mime_type,
            storage_path=str(storage_path),
            status=DocumentStatus.UPLOADED.value,
            progress_percent=0,
        )
        await self._documents.add(document)
        await self._audit.record(
            actor_id=owner_id,
            action=AuditAction.DOCUMENT_UPLOADED,
            entity_type="document",
            entity_id=str(document.id),
            payload={"filename": filename},
        )
        return document

    async def get_accessible(self, *, document_id: UUID, user: User) -> Document:
        owner_scope = None if user_has_full_tenant_access(user) else user.id
        document = await self._documents.get_with_clauses(document_id, owner_id=owner_scope)
        if document is None:
            raise NotFoundError("Document not found")
        return document

    async def list_accessible(self, *, user: User) -> list[Document]:
        if user_has_full_tenant_access(user):
            return await self._documents.list_all()
        return await self._documents.list_for_owner(user.id)

    async def get_owned(self, *, document_id: UUID, owner_id: UUID) -> Document:
        document = await self._documents.get_with_clauses(document_id, owner_id=owner_id)
        if document is None:
            raise NotFoundError("Document not found")
        return document

    async def list_owned(self, *, owner_id: UUID) -> list[Document]:
        return await self._documents.list_for_owner(owner_id)

    async def submit_for_review(self, *, document_id: UUID, user: User) -> Document:
        from datetime import UTC, datetime

        from app.models.approval import Approval
        from app.models.enums import ApprovalScope, ApprovalStatus
        from app.repositories.approval_repository import ApprovalRepository

        document = await self.get_accessible(document_id=document_id, user=user)
        if document.status != DocumentStatus.READY.value:
            raise ValidationAppError("Document must be ready before submitting for sign-off")
        document.submitted_for_review_at = datetime.now(tz=UTC)
        approvals = ApprovalRepository(self._session)
        if not await approvals.has_pending_document_approval(document_id):
            self._session.add(
                Approval(
                    scope=ApprovalScope.DOCUMENT.value,
                    status=ApprovalStatus.PENDING.value,
                    document_id=document.id,
                    clause_id=None,
                    requested_by_id=user.id,
                    notes="Submitted for general counsel review",
                ),
            )
        await self._audit.record(
            actor_id=user.id,
            action=AuditAction.DOCUMENT_SUBMITTED_REVIEW,
            entity_type="document",
            entity_id=str(document.id),
            payload={"filename": document.filename},
        )
        await self._session.flush()
        return document

    async def mark_failed(self, *, document_id: UUID, reason: str) -> None:
        document = await self._documents.get_by_id(document_id)
        if document is None:
            return
        document.status = DocumentStatus.FAILED.value
        document.failure_reason = reason
        await self._session.flush()

    async def delete_storage(self, document: Document) -> None:
        if document.storage_path is None:
            return
        path = Path(document.storage_path)
        if path.exists():
            try:
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)
            except OSError:
                return
