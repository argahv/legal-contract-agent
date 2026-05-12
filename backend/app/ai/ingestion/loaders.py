"""Format-specific loaders — reuse OCR seam from `ocr_interface` when digital text is empty."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.ai.ocr_interface import OcrProvider, StubOcrProvider
from app.core.config import get_settings
from app.core.logging_setup import get_logger

LOG = get_logger(__name__)


async def load_text_from_path(*, storage_path: str, mime_type: str | None, ocr: OcrProvider | None = None) -> str:
    """PDF/DOCX/TXT first; OCR for scanned PDFs and raster contract images (stub default)."""

    path = Path(storage_path)
    provider = ocr or StubOcrProvider()
    mime = (mime_type or "").lower()
    loop = asyncio.get_running_loop()

    if mime.startswith("image/"):
        return await provider.extract_image_text(path, mime)

    if mime.endswith("wordprocessingml.document") or path.suffix.lower() == ".docx":
        return await loop.run_in_executor(None, _read_docx, path)

    if mime == "application/pdf" or path.suffix.lower() == ".pdf":
        digital = await loop.run_in_executor(None, _read_pdf_digital, path)
        if len(digital.strip()) >= 40:
            return digital
        ocr_text = await _ocr_pdf_full(path=path, ocr=provider)
        merged = "\n".join([digital, ocr_text]).strip()
        return merged or digital

    if path.suffix.lower() in {".txt", ".md"}:
        return await loop.run_in_executor(None, path.read_text, "utf-8")

    raise ValueError(f"Unsupported mime type for extraction: {mime_type}")


def _read_docx(path: Path) -> str:
    import docx

    document = docx.Document(str(path))
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def _read_pdf_digital(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    chunks: list[str] = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        stripped = text.strip()
        if len(stripped) < 40:
            LOG.info("pdf_page_low_text", page_index=idx, path=str(path))
        chunks.append(text)
    joined = "\n".join(chunks).strip()
    settings = get_settings()
    if len(joined) > settings.extracted_text_limit_chars:
        LOG.warning("extracted_text_truncated", path=str(path), limit=settings.extracted_text_limit_chars)
        return joined[: settings.extracted_text_limit_chars]
    return joined


async def _ocr_pdf_full(*, path: Path, ocr: OcrProvider) -> str:
    """Send the entire PDF to the OCR provider (e.g. Document AI RawDocument)."""

    return await ocr.extract_pdf_text(path)
