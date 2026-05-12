"""Risk projections — aggregates per-document risk listings for reviewer dashboards."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access import can_access_owned_document
from app.core.exceptions import ForbiddenError
from app.models.risk import RiskAssessment
from app.models.user import User
from app.repositories.clause_repository import ClauseRepository
from app.repositories.contract_repository import DocumentRepository
from app.repositories.risk_repository import RiskAssessmentRepository


class RiskService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._risks = RiskAssessmentRepository(session)
        self._clauses = ClauseRepository(session)
        self._documents = DocumentRepository(session)

    async def list_for_document(self, *, document_id: UUID, user: User) -> list[RiskAssessment]:
        document = await self._documents.get_by_id(document_id)
        if document is None or not can_access_owned_document(document_owner_id=document.owner_id, user=user):
            raise ForbiddenError("Not allowed to view risks for this document")
        clauses = await self._clauses.list_for_document(document_id)
        risks: list[RiskAssessment] = []
        for clause in clauses:
            risks.extend(await self._risks.list_for_clause(clause.id))
        return risks
