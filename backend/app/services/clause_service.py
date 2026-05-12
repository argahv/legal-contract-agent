"""Clause reads — thin query surface above repositories for API pagination."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access import can_access_owned_document
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.clause import Clause
from app.models.user import User
from app.repositories.clause_repository import ClauseRepository
from app.repositories.contract_repository import DocumentRepository


class ClauseService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._clauses = ClauseRepository(session)
        self._documents = DocumentRepository(session)

    async def list_for_document(self, *, document_id: UUID, user: User) -> list[Clause]:
        owner_scope = await self._documents.get_by_id(document_id)
        if owner_scope is None or not can_access_owned_document(
            document_owner_id=owner_scope.owner_id,
            user=user,
        ):
            raise ForbiddenError("Not allowed to view clauses for this document")
        return await self._clauses.list_for_document(document_id)

    async def get_clause(self, *, clause_id: UUID, user: User) -> Clause:
        clause = await self._clauses.get_by_id(clause_id)
        if clause is None:
            raise NotFoundError("Clause not found")
        document = await self._documents.get_by_id(clause.document_id)
        if document is None or not can_access_owned_document(document_owner_id=document.owner_id, user=user):
            raise ForbiddenError("Not allowed to view clause")
        return clause
