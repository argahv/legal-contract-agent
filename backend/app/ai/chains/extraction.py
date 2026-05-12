"""LangChain clause extraction — structured output keeps downstream risk engine typed."""

from __future__ import annotations

from app.ai.llm_usage import LLMUsageRecorder
from app.ai.openai_compatible import chat_openai_kwargs
from app.ai.openai_retry import openai_retry
from app.ai.prompt_catalog import EXAMPLE_EXTRACTION_PROMPTS
from app.core.config import Settings
from app.core.logging_setup import get_logger
from app.models.enums import ClauseType
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, Field, field_validator

LOG = get_logger(__name__)


class ExtractedClause(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    title: str | None = Field(default=None, description="Human readable label if present in text")
    clause_type: ClauseType = Field(default=ClauseType.UNCATEGORIZED, description="Normalized clause bucket")
    body: str = Field(min_length=1, description="Verbatim clause text")
    confidence: float = Field(default=0.75, ge=0.0, le=1.0, description="Model self-reported certainty")

    @field_validator("clause_type", mode="before")
    @classmethod
    def coerce_clause_type(cls, value: str | ClauseType) -> ClauseType:
        if isinstance(value, ClauseType):
            return value
        try:
            return ClauseType(value)
        except ValueError:
            return ClauseType.UNCATEGORIZED


class ExtractionResult(BaseModel):
    clauses: list[ExtractedClause]


def build_extraction_chain(settings: Settings):
    """
    Chat model configured with conservative temperature + vendor retries.
    Token usage surfaces via response_metadata for finance-grade metering.
    """
    llm = ChatOpenAI(**chat_openai_kwargs(settings))
    return llm.with_structured_output(ExtractionResult)


SYSTEM_PROMPT = EXAMPLE_EXTRACTION_PROMPTS[0]["markdown"]


@openai_retry
async def extract_clauses(
    *,
    settings: Settings,
    contract_text: str,
    usage: LLMUsageRecorder | None = None,
    trace_metadata: dict[str, str] | None = None,
) -> tuple[ExtractionResult, dict[str, int]]:
    chain = build_extraction_chain(settings).with_config(
        run_name="extract_clauses",
        tags=["extraction", settings.app_name],
        metadata=trace_metadata or {},
    )
    message = SystemMessage(content=SYSTEM_PROMPT)
    human = HumanMessage(content=f"CONTRACT_TEXT:\n{contract_text}")
    result: ExtractionResult = await chain.ainvoke([message, human])
    usage_payload: dict[str, int] = {"estimated_input_chars": len(contract_text)}
    if usage is not None:
        await usage.record(
            operation="extraction.extract_clauses",
            model=settings.openai_model,
            input_units=len(contract_text),
            output_units=sum(len(c.body) for c in result.clauses),
            vendor_metadata={"clause_count": len(result.clauses)},
        )
    LOG.info("clause_extraction_complete", clause_count=len(result.clauses))
    return result, usage_payload
