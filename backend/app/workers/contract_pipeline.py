"""Background processor — FastAPI `BackgroundTasks` entrypoint bridging HTTP uploads to the AI agent."""

from __future__ import annotations

from uuid import UUID

from app.core.config import get_settings
from app.core.logging_setup import get_logger
from app.db.session import AsyncSessionLocal
from app.services.ai_pipeline import AIPipelineService
from app.services.contract_service import ContractService
from app.ws.hub import progress_hub

LOG = get_logger(__name__)


async def run_contract_pipeline(document_id: UUID, actor_id: UUID) -> None:
    """Owns session boundary + websocket fan-out for long-running review jobs."""

    settings = get_settings()

    async def notify(payload: dict[str, str | int]) -> None:
        await progress_hub.publish(document_id, payload)

    async with AsyncSessionLocal() as session:
        pipeline = AIPipelineService(session, settings)
        try:
            await pipeline.process_document(
                document_id=document_id,
                actor_id=actor_id,
                progress=notify,
            )
            await session.commit()
        except Exception as exc:
            LOG.exception("contract_pipeline_failed", document_id=str(document_id))
            await session.rollback()
            async with AsyncSessionLocal() as repair:
                contract_service = ContractService(repair, settings)
                await contract_service.mark_failed(document_id=document_id, reason=str(exc))
                await repair.commit()
            raise
