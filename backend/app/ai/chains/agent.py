"""Agent orchestration — extraction, scoring, redlines, optional LangGraph + ReAct."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import cast
from uuid import UUID

from app.ai.chains.extraction import ExtractionResult
from app.ai.chains.extraction_chain import extract_clauses_chunked
from app.ai.chains.redline_chain import propose_redline_with_playbook
from app.ai.chains.risk import llm_assess_clause, merge_levels
from app.ai.chains.rule_engine import evaluate_rules
from app.ai.embeddings import EmbeddingClient
from app.ai.ingestion.pipeline import IngestionPipeline
from app.ai.llm_usage import LLMUsageRecorder
from app.ai.vector_store import PlaybookVectorStore
from app.core.config import Settings
from app.core.logging_setup import get_logger
from app.models.approval import Approval
from app.models.clause import Clause
from app.models.document import Document
from app.models.enums import (
    ApprovalScope,
    ApprovalStatus,
    DocumentStatus,
    RedlineSource,
    RiskLevel,
)
from app.models.redline import Redline
from app.models.risk import RiskAssessment
from app.repositories.contract_repository import DocumentRepository
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

LOG = get_logger(__name__)

ProgressPublisher = Callable[[dict[str, str | int]], Awaitable[None]]


class LegalReviewAgent:
    """Coordinates deterministic + LLM stages while keeping DB side-effects explicit."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._documents = DocumentRepository(session)

    @staticmethod
    def _needs_counsel_approval(level: RiskLevel) -> bool:
        return level in {RiskLevel.HIGH, RiskLevel.CRITICAL}

    async def _run_pipeline_and_extract(
        self,
        document: Document,
        document_id: UUID,
        actor_id: UUID,
        usage: LLMUsageRecorder,
        progress: ProgressPublisher,
        trace_meta: dict[str, str],
    ) -> ExtractionResult:
        await progress({"stage": "ingestion", "percent": 5})
        document.status = DocumentStatus.PROCESSING.value
        document.progress_percent = 5
        await self._session.execute(delete(Clause).where(Clause.document_id == document_id))

        pipeline = IngestionPipeline(self._session, self._settings)
        raw_text, _chunks, _vectors = await pipeline.run(
            document=document,
            usage=usage,
            embed_chunks=not self._settings.database_url.startswith("sqlite"),
        )

        await progress({"stage": "extract", "percent": 35})
        document.progress_percent = 35
        return await extract_clauses_chunked(
            settings=self._settings,
            contract_text=raw_text,
            usage=usage,
            trace_metadata=trace_meta,
        )

    async def _run_clause_loop(
        self,
        document: Document,
        extraction: ExtractionResult,
        actor_id: UUID,
        usage: LLMUsageRecorder,
        progress: ProgressPublisher,
        trace_meta: dict[str, str],
    ) -> None:
        embedder = EmbeddingClient(self._settings, self._session, usage=usage)
        store = PlaybookVectorStore(self._session, self._settings)
        max_risk: RiskLevel = RiskLevel.LOW

        for idx, extracted in enumerate(extraction.clauses):
            clause_type_value = cast(str, extracted.clause_type)
            embedding: list[float] | None = None
            if not self._settings.database_url.startswith("sqlite"):
                vectors = await embedder.embed_texts([extracted.body])
                embedding = vectors[0]
            else:
                embedding = None

            clause = Clause(
                document_id=document.id,
                sequence=idx,
                clause_type=clause_type_value,
                title=extracted.title,
                body=extracted.body,
                confidence_score=float(extracted.confidence),
                embedding=embedding,
            )
            self._session.add(clause)
            await self._session.flush()

            rule_level, rule_hits = evaluate_rules(clause_type=clause_type_value, body=extracted.body)
            playbook_rows = await store.similar_playbook_entries_for_clause_type(
                query_embedding=embedding or [0.0] * self._settings.vector_dim,
                clause_type=clause_type_value,
                clause_body=extracted.body,
                k=4,
            )
            excerpt = playbook_rows[0].guideline if playbook_rows else None

            if self._settings.risk_use_react:
                from app.ai.chains.risk_react import llm_assess_clause_react

                judgment, _usage_meta = await llm_assess_clause_react(
                    settings=self._settings,
                    session=self._session,
                    clause_title=extracted.title,
                    clause_type=clause_type_value,
                    body=extracted.body,
                    rule_level=rule_level,
                    rule_hits=rule_hits,
                    embedding=embedding or [0.0] * self._settings.vector_dim,
                    store=store,
                    usage=usage,
                    trace_metadata=trace_meta,
                )
            else:
                judgment, _usage_meta = await llm_assess_clause(
                    settings=self._settings,
                    clause_title=extracted.title,
                    clause_type=clause_type_value,
                    body=extracted.body,
                    rule_level=rule_level,
                    rule_hits=rule_hits,
                    playbook_excerpt=excerpt,
                    usage=usage,
                    trace_metadata=trace_meta,
                    session=self._session,
                )

            model_level = (
                judgment.level
                if isinstance(judgment.level, RiskLevel)
                else RiskLevel(str(judgment.level))
            )
            final_level = merge_levels(rule_level, model_level)
            signals = list(rule_hits)
            signals.append(f"llm:{model_level.value}")

            risk_row = RiskAssessment(
                clause_id=clause.id,
                level=final_level.value,
                explanation=judgment.explanation,
                rule_hits=signals,
                token_usage={"chars": len(extracted.body)},
            )
            self._session.add(risk_row)

            if playbook_rows:
                suggestion = await propose_redline_with_playbook(
                    settings=self._settings,
                    clause_text=extracted.body,
                    clause_type=clause_type_value,
                    playbook_rows=playbook_rows,
                    usage=usage,
                    trace_metadata=trace_meta,
                )
                redline = Redline(
                    clause_id=clause.id,
                    source=RedlineSource.PLAYBOOK_RAG.value,
                    proposed_text=suggestion.suggested,
                    rationale=suggestion.explanation,
                    playbook_entry_id=suggestion.playbook_ref,
                )
                self._session.add(redline)

            if self._needs_counsel_approval(final_level):
                approval = Approval(
                    scope=ApprovalScope.CLAUSE.value,
                    status=ApprovalStatus.PENDING.value,
                    document_id=document.id,
                    clause_id=clause.id,
                    requested_by_id=actor_id,
                )
                self._session.add(approval)

            order = {
                RiskLevel.LOW: 0,
                RiskLevel.MEDIUM: 1,
                RiskLevel.HIGH: 2,
                RiskLevel.CRITICAL: 3,
            }
            if order[final_level] > order[max_risk]:
                max_risk = final_level

        document.status = DocumentStatus.READY.value
        document.progress_percent = 100
        await self._session.flush()
        await progress({"stage": "complete", "percent": 100, "max_risk": max_risk.value})
        LOG.info("legal_review_complete", document_id=str(document.id), max_risk=max_risk.value)

    async def execute(
        self,
        *,
        document_id: UUID,
        actor_id: UUID,
        usage: LLMUsageRecorder,
        progress: ProgressPublisher,
    ) -> None:
        document = await self._documents.get_with_clauses(document_id, owner_id=None)
        if document is None:
            raise ValueError("document_not_found")

        trace_meta = {
            "document_id": str(document_id),
            "user_id": str(actor_id),
        }

        if self._settings.use_langgraph_review:
            from app.ai.graph.review_graph import invoke_review_graph

            await invoke_review_graph(
                self,
                document=document,
                document_id=document_id,
                actor_id=actor_id,
                usage=usage,
                progress=progress,
                trace_meta=trace_meta,
            )
            return

        extraction = await self._run_pipeline_and_extract(
            document, document_id, actor_id, usage, progress, trace_meta
        )
        await self._run_clause_loop(
            document, extraction, actor_id, usage, progress, trace_meta
        )
