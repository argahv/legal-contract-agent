"""Reciprocal rank fusion + lightweight lexical rerank (no cross-encoder)."""

from __future__ import annotations

import re
from typing import TypeVar
from uuid import UUID

T = TypeVar("T", bound=UUID)


def reciprocal_rank_fusion(
    ranked_lists: list[list[T]],
    *,
    rrf_k: int = 60,
) -> dict[T, float]:
    """RRF score for each id appearing in one or more ranked lists."""
    scores: dict[T, float] = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (rrf_k + rank)
    return scores


_TOKEN_RE = re.compile(r"[a-z0-9]{3,}", re.IGNORECASE)


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(text or "")}


def lexical_overlap_score(query: str, document: str) -> float:
    """Cheap rerank: Jaccard-like overlap on word tokens (3+ chars)."""
    q = _tokens(query)
    d = _tokens(document)
    if not q or not d:
        return 0.0
    inter = len(q & d)
    union = len(q | d)
    return inter / union if union else 0.0


def rerank_by_lexical_overlap(
    entries: list[tuple[object, str]],
    query_text: str,
    *,
    top_k: int,
    rrf_scores: dict[UUID, float] | None = None,
) -> list:
    """
    entries: (playbook_row_id or object with id, text_for_overlap)
    """
    scored: list[tuple[float, object]] = []
    for obj, text in entries:
        lex = lexical_overlap_score(query_text, text)
        uuid_key: UUID | None = None
        if rrf_scores is not None:
            raw_id = getattr(obj, "id", obj)
            if isinstance(raw_id, UUID):
                uuid_key = raw_id
            rrf = rrf_scores.get(uuid_key, 0.0) if uuid_key else 0.0
            combined = 0.55 * rrf + 0.45 * lex
        else:
            combined = lex
        scored.append((combined, obj))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [o for _, o in scored[:top_k]]
