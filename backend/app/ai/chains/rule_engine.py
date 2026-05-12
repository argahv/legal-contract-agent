"""Deterministic policy gates before LLM narration — keeps enterprise explainability auditable."""

from __future__ import annotations

import re

from app.models.enums import ClauseType, RiskLevel

_UNLIMITED_INDEMNITY = re.compile(r"\bunlimited\b.*\bindemn", re.IGNORECASE | re.DOTALL)
_CAPS_LIABILITY = re.compile(r"cap.*liability|liability.*cap", re.IGNORECASE)
_CONSEQUENTIAL = re.compile(r"consequential|indirect damages|special damages", re.IGNORECASE)
_DATA_BREACH = re.compile(r"data breach|personal data| gdpr |dpa", re.IGNORECASE)


def _is_indemnity_family(clause_type: str) -> bool:
    return clause_type in {ClauseType.INDEMNITY.value, ClauseType.INDEMNIFICATION.value}


def _is_data_privacy_family(clause_type: str) -> bool:
    return clause_type in {
        ClauseType.CONFIDENTIALITY.value,
        ClauseType.DATA_PROTECTION.value,
    }


def evaluate_rules(*, clause_type: str, body: str) -> tuple[RiskLevel | None, list[str]]:
    hits: list[str] = []
    text = body.lower()
    level: RiskLevel | None = None

    if _is_indemnity_family(clause_type) and _UNLIMITED_INDEMNITY.search(text):
        hits.append("indemnity_unlimited_signal")
        level = RiskLevel.HIGH

    if clause_type == ClauseType.LIMITATION_OF_LIABILITY.value and _CONSEQUENTIAL.search(text):
        hits.append("consequential_damage_waiver_present")
        level = _max_level(level, RiskLevel.MEDIUM)

    if clause_type == ClauseType.LIMITATION_OF_LIABILITY.value and not _CAPS_LIABILITY.search(text):
        hits.append("liability_cap_not_detected")
        level = _max_level(level, RiskLevel.MEDIUM)

    if _is_data_privacy_family(clause_type) and _DATA_BREACH.search(text):
        hits.append("data_processing_language_under_confidentiality")
        level = _max_level(level, RiskLevel.MEDIUM)

    return level, hits


def _max_level(current: RiskLevel | None, candidate: RiskLevel) -> RiskLevel:
    order = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }
    if current is None:
        return candidate
    return candidate if order[candidate] > order[current] else current
