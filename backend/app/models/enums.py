"""Domain enumeration types — mirrored as string columns for Alembic + API portability."""

from enum import StrEnum


class UserRole(StrEnum):
    """`super_admin` is the highest privilege; provision via DB/script, not public registration."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    LEGAL_REVIEWER = "legal_reviewer"
    GENERAL_COUNSEL = "general_counsel"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ClauseType(StrEnum):
    UNCATEGORIZED = "uncategorized"
    DEFINITIONS = "definitions"
    CONFIDENTIALITY = "confidentiality"
    INDEMNITY = "indemnity"
    # Seed playbooks + extraction targets use this orthography; keep aligned with `scripts/seed_playbook.py`.
    INDEMNIFICATION = "indemnification"
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    PAYMENT_TERMS = "payment_terms"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    IP_OWNERSHIP = "ip_ownership"
    TERMINATION = "termination"
    AUTO_RENEWAL = "auto_renewal"
    GOVERNING_LAW = "governing_law"
    DATA_PROTECTION = "data_protection"
    SLA = "sla"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RedlineSource(StrEnum):
    RULE_ENGINE = "rule_engine"
    PLAYBOOK_RAG = "playbook_rag"
    LLM = "llm"


class RedlineReviewStatus(StrEnum):
    """Reviewer decisions on suggested replacement text."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalScope(StrEnum):
    DOCUMENT = "document"
    CLAUSE = "clause"


class AuditAction(StrEnum):
    LOGIN = "login"
    REGISTER = "register"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_PROCESSED = "document_processed"
    DOCUMENT_SUBMITTED_REVIEW = "document_submitted_review"
    REDLINE_UPDATED = "redline_updated"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    EXPORT = "export"
    LLM_USAGE = "llm_usage"
    TOKEN_REFRESH = "token_refresh"
