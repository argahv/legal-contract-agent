"""RAG-backed redlines — grounded in retrieved playbook rows before LLM polishes language."""

from __future__ import annotations

from uuid import UUID

from app.ai.llm_usage import LLMUsageRecorder
from app.ai.openai_compatible import chat_openai_kwargs
from app.ai.openai_retry import openai_retry
from app.ai.prompts.prompt_loader import read_prompt_file
from app.core.config import Settings
from app.core.logging_setup import get_logger
from app.models.playbook import PlaybookEntry
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

LOG = get_logger(__name__)


class RedlineSuggestion(BaseModel):
    original: str = Field(min_length=3)
    suggested: str = Field(min_length=3)
    explanation: str = Field(min_length=10)
    playbook_ref: UUID | None = Field(default=None)


@openai_retry
async def propose_redline_with_playbook(
    *,
    settings: Settings,
    clause_text: str,
    clause_type: str,
    playbook_rows: list[PlaybookEntry],
    usage: LLMUsageRecorder | None = None,
    trace_metadata: dict[str, str] | None = None,
) -> RedlineSuggestion:
    context = "\n".join(
        f"[{row.id}] {row.title}\nGUIDELINE: {row.guideline}\nPREFERRED: {row.preferred_language or ''}\n"
        for row in playbook_rows
    )
    llm = ChatOpenAI(**chat_openai_kwargs(settings, temperature=0.2))
    structured = llm.with_structured_output(RedlineSuggestion).with_config(
        run_name="redline_playbook_rag",
        tags=["redline", settings.app_name],
        metadata=trace_metadata or {},
    )
    system = SystemMessage(
        content=read_prompt_file("redline_rag.md"),
    )
    human = HumanMessage(
        content=(
            f"CLAUSE_TYPE: {clause_type}\n"
            f"PLAYBOOK_CONTEXT:\n{context or 'none'}\n"
            f"ORIGINAL_CLAUSE:\n{clause_text}\n"
            "Return JSON with original (verbatim), suggested rewrite, explanation, playbook_ref UUID if used."
        ),
    )
    suggestion: RedlineSuggestion = await structured.ainvoke([system, human])
    allowed_ids = {row.id for row in playbook_rows}
    if suggestion.playbook_ref is not None and suggestion.playbook_ref not in allowed_ids:
        suggestion = suggestion.model_copy(update={"playbook_ref": None})
    if usage is not None:
        await usage.record(
            operation="redline.propose_with_playbook",
            model=settings.openai_model,
            input_units=len(clause_text),
            output_units=len(suggestion.suggested),
            vendor_metadata={"clause_type": clause_type, "playbook_hits": len(playbook_rows)},
        )
    LOG.info("redline_suggestion_ready", has_ref=bool(suggestion.playbook_ref))
    return suggestion
