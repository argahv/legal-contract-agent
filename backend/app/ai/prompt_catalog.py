"""Curated prompt library for clause intelligence — versioned with product policy reviews."""

from __future__ import annotations

# Each entry is safe to paste into LangSmith / prompt hub experiments.
EXAMPLE_EXTRACTION_PROMPTS: list[dict[str, str]] = [
    {
        "name": "msa_clause_segmentation_v1",
        "markdown": """You are a contracts analyst. Segment the agreement into discrete clauses.
Return JSON with title, clause_type, and verbatim body for each logical provision.
Prioritize MSA-relevant topics: indemnity, liability caps, confidentiality, IP, termination, governing law.""",
    },
    {
        "name": "indemnity_scope_focus",
        "markdown": """Extract every indemnity-related clause. Classify whether it is one-way, mutual, or carve-out.
Surface survival language and any caps or baskets reference.""",
    },
    {
        "name": "limitation_of_liability_inventory",
        "markdown": """Find all limitation of liability sections. Capture carve-outs (fraud, gross negligence, IP),
whether damages are limited to fees, and if consequential damages are waived.""",
    },
    {
        "name": "payment_and_sla_crosswalk",
        "markdown": """Identify payment terms, fee schedules, late interest, and SLA / availability commitments.
Link penalties or service credits if present.""",
    },
    {
        "name": "data_protection_addendum_scan",
        "markdown": """Pull clauses governing personal data, subprocessors, security measures, breach notice,
and audit rights even if titled as a DPA exhibit.""",
    },
    {
        "name": "ip_and_license_grants",
        "markdown": """Capture IP ownership, license grants (directionality), moral rights waivers,
and any open-source policy references.""",
    },
    {
        "name": "termination_and_transition",
        "markdown": """Segment termination triggers, cure periods, effects of expiration, survival schedules,
data return/deletion, and transition assistance expectations.""",
    },
    {
        "name": "change_of_control_sensitive",
        "markdown": """Flag assignment, change-of-control, non-solicitation, and exclusivity language.
Treat these as escalation candidates for playbook alignment.""",
    },
]
