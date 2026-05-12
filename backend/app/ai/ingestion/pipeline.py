"""Ingestion pipeline façade — deterministic load + chunk boundaries shared by extraction map steps."""

from __future__ import annotations

from app.ai.embeddings import EmbeddingClient
from app.ai.ingestion.chunker import legal_chunker
from app.ai.ingestion.loaders import load_text_from_path
from app.ai.llm_usage import LLMUsageRecorder
from app.ai.ocr_interface import OcrProvider, StubOcrProvider
from app.core.config import Settings
from app.core.logging_setup import get_logger
from app.models.document import Document
from sqlalchemy.ext.asyncio import AsyncSession

LOG = get_logger(__name__)


class IngestionPipeline:
    """Loads raw text, persists it on the document, prepares chunk windows + optional embeddings."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._chunks = legal_chunker()
        self._ocr_provider: OcrProvider | None = None

    def _get_ocr_provider(self) -> OcrProvider:
        if self._ocr_provider is not None:
            return self._ocr_provider
        s = self._settings
        project = (s.google_docai_project_id or "").strip()
        processor = (s.google_docai_processor_id or "").strip()
        location = (s.google_docai_location or "").strip() or "us"
        if project and processor and location:
            from app.ai.ocr_google_docai import GoogleDocumentAIOcrProvider

            self._ocr_provider = GoogleDocumentAIOcrProvider(s)
        else:
            self._ocr_provider = StubOcrProvider()
        return self._ocr_provider

    async def run(
        self,
        *,
        document: Document,
        usage: LLMUsageRecorder | None = None,
        embed_chunks: bool = True,
    ) -> tuple[str, list[str], list[list[float]]]:
        if document.storage_path is None:
            raise ValueError("document missing storage_path")

        raw = await load_text_from_path(
            storage_path=document.storage_path,
            mime_type=document.mime_type,
            ocr=self._get_ocr_provider(),
        )
        document.extracted_text = raw
        chunks = self._chunks.split_text(raw)
        if embed_chunks and not self._settings.database_url.startswith("sqlite"):
            embedder = EmbeddingClient(self._settings, self._session, usage=usage)
            vectors = await embedder.embed_texts(chunks)
        else:
            vectors = []
        await self._session.flush()
        LOG.info("ingestion_complete", document_id=str(document.id), chunks=len(chunks))
        return raw, chunks, vectors
