"""Probabilistic risk narration layered atop deterministic hits — dual signal for reviewers."""

from __future__ import annotations

from app.ai.llm_usage import LLMUsageRecorder
from app.ai.openai_compatible import chat_openai_kwargs
from app.ai.openai_retry import openai_retry
from app.core.config import Settings
from app.core.logging_setup import get_logger
from app.models.enums import RiskLevel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

LOG = get_logger(__name__)


class LlmRiskJudgment(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    level: RiskLevel
    explanation: str = Field(min_length=20)


def build_risk_chain(settings: Settings):
    llm = ChatOpenAI(**chat_openai_kwargs(settings, temperature=0.0))
    return llm.with_structured_output(LlmRiskJudgment)


@openai_retry
async def llm_assess_clause(
    *,
    settings: Settings,
    clause_title: str | None,
    clause_type: str,
    body: str,
    rule_level: RiskLevel | None,
    rule_hits: list[str],
    playbook_excerpt: str | None,
    usage: LLMUsageRecorder | None = None,
    trace_metadata: dict[str, str] | None = None,
    session: AsyncSession | None = None,
) -> tuple[LlmRiskJudgment, dict[str, int]]:
    from app.ai.risk_cache import (
        get_cached_risk_judgment,
        put_cached_risk_judgment,
        risk_judgment_cache_key,
    )

    cache_key = risk_judgment_cache_key(
        settings=settings,
        clause_type=clause_type,
        body=body,
        rule_level=rule_level,
        rule_hits=rule_hits,
        playbook_excerpt=playbook_excerpt,
    )
    if (
        session is not None
        and settings.risk_judgment_cache_enabled
        and not settings.risk_use_react
    ):
        cached = await get_cached_risk_judgment(session, key_hash=cache_key, settings=settings)
        if cached is not None:
            LOG.info("risk_judgment_cache_hit", clause_type=clause_type)
            if usage is not None:
                await usage.record(
                    operation="risk.llm_assess_clause.cached",
                    model=settings.openai_model,
                    input_units=len(body),
                    output_units=0,
                    vendor_metadata={"clause_type": clause_type, "cached": True},
                )
            return cached, {"cached": True}

    chain = build_risk_chain(settings).with_config(
        run_name="risk_assess_clause",
        tags=["risk", settings.app_name],
        metadata=trace_metadata or {},
    )
    system = SystemMessage(
        content=(
            "You are an experienced commercial counsel. Combine rule hits with contract text. "
            "Escalate risk when indemnity is uncapped, liability caps missing, or data breach exposure unclear. "
            "Always ground the explanation in concrete language from the clause."
        ),
    )
    human = HumanMessage(
        content=(
            f"CLAUSE_TYPE: {clause_type}\n"
            f"TITLE: {clause_title}\n"
            f"RULE_LEVEL: {rule_level.value if rule_level else 'none'}\n"
            f"RULE_HITS: {', '.join(rule_hits) or 'none'}\n"
            f"PLAYBOOK_HINT:\n{playbook_excerpt or 'n/a'}\n"
            f"CLAUSE BODY:\n{body}"
        ),
    )
    judgment: LlmRiskJudgment = await chain.ainvoke([system, human])
    usage_payload: dict[str, int] = {"risk_chars": len(body)}
    if usage is not None:
        await usage.record(
            operation="risk.llm_assess_clause",
            model=settings.openai_model,
            input_units=len(body),
            output_units=len(judgment.explanation),
            vendor_metadata={"clause_type": clause_type},
        )
    if (
        session is not None
        and settings.risk_judgment_cache_enabled
        and not settings.risk_use_react
    ):
        await put_cached_risk_judgment(
            session,
            key_hash=cache_key,
            settings=settings,
            judgment=judgment,
        )
    LOG.info("risk_judgement_emitted", level=judgment.level)
    return judgment, usage_payload


def merge_levels(rule_level: RiskLevel | None, model_level: RiskLevel) -> RiskLevel:
    order = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }
    if rule_level is None:
        return model_level
    return model_level if order[model_level] >= order[rule_level] else rule_level
