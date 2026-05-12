from app.ai.chains.rule_engine import evaluate_rules
from app.models.enums import ClauseType, RiskLevel


def test_rule_engine_indemnity_signal() -> None:
    level, hits = evaluate_rules(
        clause_type=ClauseType.INDEMNIFICATION.value,
        body="Customer grants Vendor an unlimited indemnity for all claims.",
    )
    assert level == RiskLevel.HIGH
    assert "indemnity_unlimited_signal" in hits
