"""Repository module surface — data-access adapters behind explicit service transactions."""

from app.repositories.approval_repository import ApprovalRepository
from app.repositories.audit_repository import AuditLogRepository
from app.repositories.clause_repository import ClauseRepository
from app.repositories.contract_repository import DocumentRepository
from app.repositories.playbook_repository import PlaybookRepository
from app.repositories.redline_repository import RedlineRepository
from app.repositories.risk_repository import RiskAssessmentRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "ApprovalRepository",
    "AuditLogRepository",
    "ClauseRepository",
    "DocumentRepository",
    "PlaybookRepository",
    "RedlineRepository",
    "RiskAssessmentRepository",
    "UserRepository",
]
