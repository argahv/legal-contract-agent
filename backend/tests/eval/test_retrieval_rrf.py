"""Retrieval quality helpers — RRF fusion (unit-testable without Postgres)."""

from __future__ import annotations

from uuid import UUID, uuid4

from app.ai.retrieval.rrf import reciprocal_rank_fusion, rerank_by_lexical_overlap


def test_rrf_prefers_both_lists() -> None:
    a, b, c = uuid4(), uuid4(), uuid4()
    vec = [a, b, c]
    lex = [b, a]
    fused = reciprocal_rank_fusion([vec, lex], rrf_k=60)
    assert fused[b] > fused[c]


def test_lexical_rerank_orders_by_overlap() -> None:
    class Row:
        def __init__(self, uid: UUID) -> None:
            self.id = uid

    r1, r2 = Row(uuid4()), Row(uuid4())
    fused = {r1.id: 0.9, r2.id: 0.8}
    q = "indemnification cap liability unlimited"
    out = rerank_by_lexical_overlap(
        [
            (r2, "Cookies and analytics preferences."),
            (r1, "Unlimited indemnification without monetary cap for third-party claims."),
        ],
        q,
        top_k=2,
        rrf_scores=fused,
    )
    assert out[0] is r1
