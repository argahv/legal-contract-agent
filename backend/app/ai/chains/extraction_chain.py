"""Chunked extraction — map step runs structured JSON across windows; reduce merges duplicates."""

from __future__ import annotations

from app.ai.chains.extraction import ExtractedClause, ExtractionResult
from app.ai.ingestion.chunker import legal_chunker
from app.ai.llm_usage import LLMUsageRecorder
from app.ai.openai_compatible import chat_openai_kwargs
from app.ai.openai_retry import openai_retry
from app.ai.prompts.prompt_loader import read_prompt_file
from app.core.config import Settings
from app.core.logging_setup import get_logger
from app.models.enums import ClauseType
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

LOG = get_logger(__name__)

_SEVEN_TYPES: set[str] = {
    ClauseType.LIMITATION_OF_LIABILITY.value,
    ClauseType.INDEMNIFICATION.value,
    ClauseType.GOVERNING_LAW.value,
    ClauseType.TERMINATION.value,
    ClauseType.INTELLECTUAL_PROPERTY.value,
    ClauseType.CONFIDENTIALITY.value,
    ClauseType.DATA_PROTECTION.value,
}


def _dedupe(clauses: list[ExtractedClause]) -> list[ExtractedClause]:
    seen: set[tuple[str, str]] = set()
    merged: list[ExtractedClause] = []
    for clause in clauses:
        key = (str(clause.clause_type), clause.body.strip()[:160])
        if key in seen:
            continue
        if str(clause.clause_type) in _SEVEN_TYPES or str(clause.clause_type) == ClauseType.UNCATEGORIZED.value:
            seen.add(key)
            merged.append(clause)
    return merged


@openai_retry
async def extract_clauses_chunked(
    *,
    settings: Settings,
    contract_text: str,
    usage: LLMUsageRecorder | None = None,
    trace_metadata: dict[str, str] | None = None,
) -> ExtractionResult:
    splitter = legal_chunker()
    chunks = splitter.split_text(contract_text)
    system = SystemMessage(content=read_prompt_file("extraction_map_reduce.md"))
    llm = ChatOpenAI(**chat_openai_kwargs(settings))
    structured = llm.with_structured_output(ExtractionResult).with_config(
        run_name="extract_clauses_chunk",
        tags=["extraction", "map_reduce", settings.app_name],
        metadata=trace_metadata or {},
    )

    aggregated: list[ExtractedClause] = []
    for idx, chunk in enumerate(chunks):
        human = HumanMessage(
            content=f"CHUNK_INDEX: {idx}\nCHUNK_TOTAL: {len(chunks)}\nCHUNK_TEXT:\n{chunk}",
        )
        part: ExtractionResult = await structured.ainvoke([system, human])
        aggregated.extend(part.clauses)

    if usage is not None:
        await usage.record(
            operation="extraction.extract_clauses_chunked",
            model=settings.openai_model,
            input_units=len(contract_text),
            output_units=len(chunks),
            vendor_metadata={"chunk_count": len(chunks), "raw_hits": len(aggregated)},
        )

    deduped = _dedupe(aggregated)
    LOG.info("chunked_extraction_complete", raw=len(aggregated), deduped=len(deduped))
    return ExtractionResult(clauses=deduped)
