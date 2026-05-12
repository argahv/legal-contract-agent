"""Risk LLM output cache (semantic / deterministic key — not embedding distance)."""

from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.risk import LlmRiskJudgment
from app.core.config import Settings
from app.models.enums import RiskLevel
from app.models.risk_judgment_cache import RiskJudgmentCache


def risk_judgment_cache_key(
    *,
    settings: Settings,
    clause_type: str,
    body: str,
    rule_level: RiskLevel | None,
    rule_hits: list[str],
    playbook_excerpt: str | None,
) -> str:
    rule = rule_level.value if rule_level else "none"
    hits = ",".join(sorted(rule_hits))
    hint = playbook_excerpt or ""
    raw = (
        f"{settings.risk_prompt_version}|{settings.openai_model}|"
        f"{clause_type}|{rule}|{hits}|{hint}|{body}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def get_cached_risk_judgment(
    session: AsyncSession,
    *,
    key_hash: str,
    settings: Settings,
) -> LlmRiskJudgment | None:
    row = await session.scalar(
        select(RiskJudgmentCache).where(RiskJudgmentCache.key_hash == key_hash)
    )
    if row is None:
        return None
    if row.model_name != settings.openai_model or row.prompt_version != settings.risk_prompt_version:
        return None
    try:
        level = RiskLevel(row.level)
    except ValueError:
        return None
    return LlmRiskJudgment(level=level, explanation=row.explanation)


async def put_cached_risk_judgment(
    session: AsyncSession,
    *,
    key_hash: str,
    settings: Settings,
    judgment: LlmRiskJudgment,
) -> None:
    lvl = judgment.level.value if isinstance(judgment.level, RiskLevel) else str(judgment.level)
    row = RiskJudgmentCache(
        key_hash=key_hash,
        model_name=settings.openai_model,
        prompt_version=settings.risk_prompt_version,
        level=lvl,
        explanation=judgment.explanation,
    )
    await session.merge(row)
    await session.flush()
