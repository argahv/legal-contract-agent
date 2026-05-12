"""Embedding client — batches OpenAI embedding calls with sha256 L1 memory + JSON DB cache."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Sequence

from app.ai.llm_usage import LLMUsageRecorder
from app.ai.openai_compatible import create_embeddings_sync
from app.ai.openai_retry import openai_retry
from app.core.config import Settings
from app.core.logging_setup import get_logger
from app.models.embedding_cache import EmbeddingCache
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

LOG = get_logger(__name__)


def _sha256_key(text: str, model_name: str) -> str:
    payload = f"{model_name}\n{text}".encode()
    return hashlib.sha256(payload).hexdigest()


class EmbeddingClient:
    """Async-friendly façade around OpenAI-compatible ``/embeddings`` + hot RAM + SQL cache."""

    def __init__(
        self,
        settings: Settings,
        session: AsyncSession,
        *,
        usage: LLMUsageRecorder | None = None,
    ) -> None:
        self._settings = settings
        self._session = session
        self._usage = usage
        self._memory: dict[str, list[float]] = {}
        # Settings.strip_openai_api_key ensures a single non-whitespace bearer (see config).
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key

    @openai_retry
    async def _embed_batch_uncached(self, texts: list[str]) -> list[list[float]]:
        def _call() -> list[list[float]]:
            return create_embeddings_sync(self._settings, texts)

        import asyncio

        loop = asyncio.get_running_loop()
        vectors: list[list[float]] = await loop.run_in_executor(None, _call)

        if self._usage is not None:
            approx_tokens = sum(len(t) for t in texts) // 4
            await self._usage.record(
                operation="embedding.embed_documents",
                model=self._settings.openai_embedding_model,
                input_units=approx_tokens,
                output_units=len(texts) * self._settings.vector_dim,
                vendor_metadata={"batch_size": len(texts)},
            )
        return vectors

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._settings.openai_embedding_model
        results: list[list[float] | None] = [None] * len(texts)
        pending_idx: list[int] = []
        pending_texts: list[str] = []

        for idx, text in enumerate(texts):
            key = _sha256_key(text, model)
            if key in self._memory:
                results[idx] = self._memory[key]
                continue
            cached = await self._session.scalar(
                select(EmbeddingCache.vector).where(
                    EmbeddingCache.key_hash == key,
                    EmbeddingCache.model_name == model,
                )
            )
            if cached is not None:
                self._memory[key] = cached
                results[idx] = cached
                continue
            pending_idx.append(idx)
            pending_texts.append(text)

        if pending_texts:
            batch_size = 32
            for start in range(0, len(pending_texts), batch_size):
                chunk = pending_texts[start : start + batch_size]
                chunk_idx = pending_idx[start : start + batch_size]
                fresh = await self._embed_batch_uncached(chunk)
                for local_i, vec in enumerate(fresh):
                    global_idx = chunk_idx[local_i]
                    text = texts[global_idx]
                    key = _sha256_key(text, model)
                    self._memory[key] = vec
                    await self._session.merge(
                        EmbeddingCache(
                            key_hash=key,
                            model_name=model,
                            dims=self._settings.vector_dim,
                            vector=vec,
                        )
                    )
                    results[global_idx] = vec
            await self._session.flush()

        filled: list[list[float]] = []
        for vec in results:
            if vec is None:
                raise RuntimeError("embedding pipeline failed to populate a vector slot")
            filled.append(vec)
        return filled

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]

    async def clear_memory_for_tests(self) -> None:
        """Test helper — avoids cross-test pollution without requiring process isolation."""

        self._memory.clear()
        await self._session.execute(delete(EmbeddingCache))
        await self._session.commit()
