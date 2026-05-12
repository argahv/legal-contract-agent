"""Playbook admin service — couples CRUD with embedding refresh for retrieval parity."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import EmbeddingClient
from app.core.config import Settings
from app.core.exceptions import NotFoundError
from app.models.playbook import PlaybookEntry
from app.repositories.playbook_repository import PlaybookRepository
from app.schemas.playbook import PlaybookCreate, PlaybookUpdate


class PlaybookService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._repo = PlaybookRepository(session)

    async def _embed_entry(self, entry: PlaybookEntry) -> None:
        if self._settings.database_url.startswith("sqlite"):
            entry.embedding = None
            return
        embedder = EmbeddingClient(self._settings, self._session, usage=None)
        payload = f"{entry.title}\n{entry.guideline}\n{entry.preferred_language or ''}"
        vectors = await embedder.embed_texts([payload])
        entry.embedding = vectors[0]

    async def create(self, *, payload: PlaybookCreate) -> PlaybookEntry:
        entry = PlaybookEntry(
            title=payload.title,
            clause_type=payload.clause_type.value,
            guideline=payload.guideline,
            preferred_language=payload.preferred_language,
            embedding=None,
        )
        await self._repo.add(entry)
        await self._embed_entry(entry)
        await self._session.flush()
        return entry

    async def update(self, *, entry_id: UUID, payload: PlaybookUpdate) -> PlaybookEntry:
        entry = await self._repo.get_by_id(entry_id)
        if entry is None:
            raise NotFoundError("Playbook entry not found")
        if payload.title is not None:
            entry.title = payload.title
        if payload.clause_type is not None:
            entry.clause_type = payload.clause_type.value
        if payload.guideline is not None:
            entry.guideline = payload.guideline
        if payload.preferred_language is not None:
            entry.preferred_language = payload.preferred_language
        await self._embed_entry(entry)
        await self._session.flush()
        return entry

    async def delete(self, *, entry_id: UUID) -> None:
        entry = await self._repo.get_by_id(entry_id)
        if entry is None:
            raise NotFoundError("Playbook entry not found")
        await self._repo.delete(entry)

    async def list_entries(self) -> list[PlaybookEntry]:
        return await self._repo.list_all_entries(limit=500, offset=0)

    async def get(self, *, entry_id: UUID) -> PlaybookEntry:
        entry = await self._repo.get_by_id(entry_id)
        if entry is None:
            raise NotFoundError("Playbook entry not found")
        return entry
