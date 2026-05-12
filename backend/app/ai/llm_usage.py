"""LLM usage accounting — every vendor call funnels through this recorder for audit + finance hooks."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from app.core.logging_setup import get_logger
from app.models.enums import AuditAction
from app.services.audit_service import AuditService
from sqlalchemy.ext.asyncio import AsyncSession

LOG = get_logger(__name__)


class LLMUsageRecorder:
    """Persists high-signal usage metadata to `audit_logs` while mirroring to structured logs."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        actor_id: UUID | None,
        document_id: UUID | None,
        tenant_id: UUID | None = None,
    ) -> None:
        self._audit = AuditService(session)
        self._actor_id = actor_id
        self._document_id = document_id
        self._tenant_id = tenant_id

    async def record(
        self,
        *,
        operation: str,
        model: str,
        input_units: int | None = None,
        output_units: int | None = None,
        vendor_metadata: Mapping[str, object] | None = None,
    ) -> None:
        payload: dict[str, object] = {
            "operation": operation,
            "model": model,
            "input_units": input_units,
            "output_units": output_units,
            "document_id": str(self._document_id) if self._document_id else None,
            "tenant_id": str(self._tenant_id) if self._tenant_id else None,
            "vendor_metadata": dict(vendor_metadata) if vendor_metadata is not None else {},
        }
        entity_id = str(self._document_id or self._actor_id or "unknown")
        await self._audit.record(
            actor_id=self._actor_id,
            action=AuditAction.LLM_USAGE,
            entity_type="llm_call",
            entity_id=entity_id,
            payload=payload,
        )
        LOG.info(
            "llm_usage_recorded",
            operation=operation,
            model=model,
            input_units=input_units,
            output_units=output_units,
            document_id=str(self._document_id) if self._document_id else None,
        )
