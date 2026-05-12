"""AI pipeline service — wraps the LangGraph-style agent with audit completion markers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.agent import LegalReviewAgent
from app.ai.llm_usage import LLMUsageRecorder
from app.core.config import Settings
from app.core.logging_setup import get_logger
from app.models.enums import AuditAction
from app.services.audit_service import AuditService

LOG = get_logger(__name__)


class AIPipelineService:
    """Allows FastAPI workers and integration tests to call the same orchestration entrypoint."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def process_document(
        self,
        *,
        document_id: UUID,
        actor_id: UUID,
        progress,
    ) -> None:
        usage = LLMUsageRecorder(self._session, actor_id=actor_id, document_id=document_id)
        agent = LegalReviewAgent(self._session, self._settings)
        audit = AuditService(self._session)

        try:
            await agent.execute(
                document_id=document_id,
                actor_id=actor_id,
                usage=usage,
                progress=progress,
            )
            await audit.record(
                actor_id=actor_id,
                action=AuditAction.DOCUMENT_PROCESSED,
                entity_type="document",
                entity_id=str(document_id),
            )
        except Exception:
            LOG.exception("document_pipeline_failed", document_id=str(document_id))
            raise
