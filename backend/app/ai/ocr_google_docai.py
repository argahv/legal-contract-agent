"""Google Cloud Document AI OCR — full-PDF `process_document` (no page rasterization)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from google.cloud import documentai_v1 as documentai

from app.ai.ocr_interface import OcrProvider
from app.core.config import Settings


class GoogleDocumentAIOcrProvider(OcrProvider):
    """Runs synchronous Document AI client calls in a thread pool."""

    def __init__(self, settings: Settings) -> None:
        project = (settings.google_docai_project_id or "").strip()
        processor = (settings.google_docai_processor_id or "").strip()
        location = (settings.google_docai_location or "").strip() or "us"
        if not project:
            raise ValueError("Google Document AI requires a non-empty google_docai_project_id")
        if not processor:
            raise ValueError("Google Document AI requires a non-empty google_docai_processor_id")
        self._project_id = project
        self._processor_id = processor
        self._location = location

    async def extract_pdf_text(self, pdf_path: Path) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._extract_pdf_text_sync, pdf_path)

    def _extract_pdf_text_sync(self, pdf_path: Path) -> str:
        pdf_bytes = pdf_path.read_bytes()
        return self._process_raw_document_sync(pdf_bytes, "application/pdf")

    async def extract_image_text(self, image_path: Path, mime_type: str) -> str:
        loop = asyncio.get_running_loop()
        normalized = (mime_type or "application/octet-stream").strip().lower()
        return await loop.run_in_executor(None, self._extract_image_text_sync, image_path, normalized)

    def _extract_image_text_sync(self, image_path: Path, mime_type: str) -> str:
        image_bytes = image_path.read_bytes()
        return self._process_raw_document_sync(image_bytes, mime_type)

    def _process_raw_document_sync(self, content: bytes, mime_type: str) -> str:
        client = documentai.DocumentProcessorServiceClient()
        name = client.processor_path(self._project_id, self._location, self._processor_id)
        raw_document = documentai.RawDocument(content=content, mime_type=mime_type)
        request = documentai.ProcessRequest(name=name, raw_document=raw_document)
        result = client.process_document(request=request)
        return (result.document.text or "").strip()

    async def extract_pdf_page_text(self, pdf_path: Path, page_index: int) -> str:  # noqa: ARG002
        raise NotImplementedError(
            "GoogleDocumentAIOcrProvider uses extract_pdf_text (full-document OCR) only"
        )
