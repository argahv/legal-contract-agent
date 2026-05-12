"""Embed playbook rows for pgvector RAG — fills NULL `embedding` via OpenAI-compatible API."""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.ai.embeddings import EmbeddingClient
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.playbook import PlaybookEntry
from sqlalchemy import select


def _playbook_text(row: PlaybookEntry) -> str:
    parts = [row.title, row.clause_type, row.guideline]
    if row.preferred_language:
        parts.append(row.preferred_language)
    return "\n\n".join(parts)


async def _run(*, force_all: bool) -> int:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        stmt = select(PlaybookEntry).order_by(PlaybookEntry.created_at.asc())
        result = await session.execute(stmt)
        rows = list(result.scalars().all())
        if not rows:
            print("No playbook rows — run: python -m scripts.seed_playbook")
            return 1

        targets = rows if force_all else [r for r in rows if r.embedding is None]
        if not targets:
            print("All playbook rows already have embeddings (use --force to re-embed).")
            return 0

        client = EmbeddingClient(settings, session, usage=None)
        texts = [_playbook_text(r) for r in targets]
        vectors = await client.embed_texts(texts)
        for row, vec in zip(targets, vectors, strict=True):
            row.embedding = vec
        await session.commit()
        print(f"Embedded {len(targets)} playbook row(s) with model={settings.openai_embedding_model}.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate playbook_entries.embedding for vector search.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-embed every row even if embedding is already set.",
    )
    args = parser.parse_args()
    try:
        raise SystemExit(asyncio.run(_run(force_all=args.force)))
    except Exception as exc:
        print(f"embed_playbook_vectors failed: {exc}", file=sys.stderr)
        print(
            "Hint: DATABASE_URL must reach Postgres; OPENROUTER_* or OPENAI_* must allow embeddings API.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
