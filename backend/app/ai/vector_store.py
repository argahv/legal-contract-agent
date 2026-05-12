"""pgvector retrieval — dense, hybrid (dense+FTS+RRF), and lexical rerank."""

from __future__ import annotations

from uuid import UUID

from app.ai.retrieval.rrf import reciprocal_rank_fusion, rerank_by_lexical_overlap
from app.core.config import Settings
from app.core.logging_setup import get_logger
from app.models.playbook import PlaybookEntry
from sqlalchemy import Select, case, select, text
from sqlalchemy.ext.asyncio import AsyncSession

LOG = get_logger(__name__)


def _vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"


def _fts_query_snippet(clause_body: str) -> str:
    raw = " ".join((clause_body or "").split())
    if not raw:
        return ""
    return raw[:500]


class PlaybookVectorStore:
    """Cosine-distance retrieval; Postgres supports hybrid FTS + RRF + overlap rerank."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    def _is_sqlite(self) -> bool:
        return self._settings.database_url.startswith("sqlite")

    def _use_hybrid(self) -> bool:
        if self._is_sqlite():
            return False
        return self._settings.hybrid_playbook_retrieval

    async def similar_playbook_entries(self, *, query_embedding: list[float], k: int = 5) -> list[PlaybookEntry]:
        if self._is_sqlite():
            LOG.info("vector_search_skipped", reason="sqlite_backend")
            return []

        distance = PlaybookEntry.embedding.cosine_distance(query_embedding)  # type: ignore[attr-defined]
        stmt: Select[tuple[PlaybookEntry]] = (
            select(PlaybookEntry)
            .where(PlaybookEntry.embedding.is_not(None))
            .order_by(distance)
            .limit(k)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def _similar_vector_only(
        self,
        *,
        query_embedding: list[float],
        clause_type: str,
        k: int,
    ) -> list[PlaybookEntry]:
        distance = PlaybookEntry.embedding.cosine_distance(query_embedding)  # type: ignore[attr-defined]
        type_rank = case(
            (PlaybookEntry.clause_type == clause_type, 0),
            else_=1,
        )
        stmt = (
            select(PlaybookEntry)
            .where(PlaybookEntry.embedding.is_not(None))
            .order_by(type_rank, distance)
            .limit(k)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def _similar_hybrid(
        self,
        *,
        query_embedding: list[float],
        clause_type: str,
        clause_body: str,
        k: int,
    ) -> list[PlaybookEntry]:
        lim_v = self._settings.playbook_retrieval_vector_pool
        lim_l = self._settings.playbook_retrieval_lex_pool
        vec_lit = _vector_literal(query_embedding)

        vec_sql = text(
            """
            SELECT id::text AS id
            FROM playbook_entries
            WHERE embedding IS NOT NULL AND clause_type = :ct
            ORDER BY embedding <=> CAST(:emb AS vector) ASC
            LIMIT :lim
            """
        )
        v_rows = await self._session.execute(
            vec_sql, {"emb": vec_lit, "ct": clause_type, "lim": lim_v}
        )
        vec_ids = [UUID(row[0]) for row in v_rows.fetchall()]

        lex_ids: list[UUID] = []
        fts_q = _fts_query_snippet(clause_body)
        if fts_q:
            fts_sql = text(
                """
                SELECT id::text AS id
                FROM playbook_entries
                WHERE embedding IS NOT NULL
                  AND clause_type = :ct
                  AND search_vector @@ plainto_tsquery('english', :q)
                ORDER BY ts_rank_cd(search_vector, plainto_tsquery('english', :q)) DESC
                LIMIT :lim
                """
            )
            try:
                l_rows = await self._session.execute(
                    fts_sql, {"q": fts_q, "ct": clause_type, "lim": lim_l}
                )
                lex_ids = [UUID(row[0]) for row in l_rows.fetchall()]
            except Exception:
                LOG.warning("playbook_fts_query_failed", exc_info=True)
                lex_ids = []

        if not lex_ids:
            ranked_lists: list[list[UUID]] = [vec_ids]
        else:
            ranked_lists = [vec_ids, lex_ids]

        fused = reciprocal_rank_fusion(ranked_lists, rrf_k=self._settings.playbook_retrieval_rrf_k)
        if not fused:
            return []

        ordered = sorted(fused.keys(), key=lambda i: fused[i], reverse=True)[
            : self._settings.playbook_rerank_top_n
        ]
        stmt = select(PlaybookEntry).where(PlaybookEntry.id.in_(ordered))
        result = await self._session.execute(stmt)
        by_id: dict[UUID, PlaybookEntry] = {r.id: r for r in result.scalars().all()}
        candidates = [by_id[i] for i in ordered if i in by_id]
        tuples: list[tuple[PlaybookEntry, str]] = [
            (e, f"{e.title}\n{e.guideline}") for e in candidates
        ]
        return rerank_by_lexical_overlap(
            tuples,
            clause_body,
            top_k=k,
            rrf_scores=fused,
        )

    async def similar_playbook_entries_for_clause_type(
        self,
        *,
        query_embedding: list[float],
        clause_type: str,
        k: int = 5,
        clause_body: str | None = None,
    ) -> list[PlaybookEntry]:
        if self._is_sqlite():
            return []

        if not self._use_hybrid() or not clause_body:
            return await self._similar_vector_only(
                query_embedding=query_embedding, clause_type=clause_type, k=k
            )

        try:
            return await self._similar_hybrid(
                query_embedding=query_embedding,
                clause_type=clause_type,
                clause_body=clause_body,
                k=k,
            )
        except Exception:
            LOG.warning("hybrid_retrieval_fallback_vector", exc_info=True)
            return await self._similar_vector_only(
                query_embedding=query_embedding, clause_type=clause_type, k=k
            )
