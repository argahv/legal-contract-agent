"""Approval queue — encodes dual-control transitions for HIGH/CRITICAL escalations."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.approval import Approval
from app.models.enums import ApprovalStatus, AuditAction, UserRole
from app.repositories.approval_repository import ApprovalRepository
from app.schemas.approval import ApprovalDecision, ApprovalRead
from app.services.audit_service import AuditService


class ApprovalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._approvals = ApprovalRepository(session)

    @staticmethod
    def to_read(approval: Approval) -> ApprovalRead:
        """Build API DTO with joined document/requester fields when loaded."""
        data = ApprovalRead.model_validate(approval).model_dump()
        doc = approval.document
        if doc is not None:
            data["document_filename"] = doc.filename
            data["document_status"] = doc.status
            data["document_uploaded_at"] = doc.created_at
        req_by = approval.requested_by
        if req_by is not None:
            data["requested_by_email"] = req_by.email
        return ApprovalRead(**data)

    async def list_pending(self, *, actor_role: UserRole) -> list[ApprovalRead]:
        if actor_role not in {
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.GENERAL_COUNSEL,
        }:
            raise ForbiddenError(
                "Only super administrators, administrators, or general counsel can list pending approvals",
            )
        rows = await self._approvals.list_pending_for_counsel()
        return [self.to_read(row) for row in rows]

    async def decide(
        self,
        *,
        approval_id: UUID,
        payload: ApprovalDecision,
        reviewer_id: UUID,
        actor_role: UserRole,
    ) -> Approval:
        if actor_role not in {
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.GENERAL_COUNSEL,
        }:
            raise ForbiddenError(
                "Only super administrators, administrators, or general counsel can decide approvals",
            )
        approval = await self._approvals.get_by_id(approval_id)
        if approval is None:
            raise NotFoundError("Approval not found")
        if approval.status != ApprovalStatus.PENDING.value:
            raise ValidationAppError("Approval already decided")

        if payload.decision not in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED}:
            raise ValidationAppError("Invalid decision")

        approval.status = payload.decision.value
        approval.reviewer_id = reviewer_id
        approval.notes = payload.comment
        approval.decided_at = datetime.now(tz=UTC)
        await self._session.flush()

        audit = AuditService(self._session)
        action = (
            AuditAction.APPROVAL_GRANTED
            if payload.decision == ApprovalStatus.APPROVED
            else AuditAction.APPROVAL_REJECTED
        )
        await audit.record(
            actor_id=reviewer_id,
            action=action,
            entity_type="approval",
            entity_id=str(approval.id),
            payload={"comment": payload.comment},
        )
        return approval
