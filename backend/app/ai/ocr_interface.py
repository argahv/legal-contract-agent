"""Document text extraction — OCR is intentionally pluggable; digital PDFs bypass raster cost."""

from abc import ABC, abstractmethod
from pathlib import Path


class OcrProvider(ABC):
    """Optical character recognition hook for image-only / poor-digital PDF lanes."""

    @abstractmethod
    async def extract_pdf_page_text(self, pdf_path: Path, page_index: int) -> str:
        """Return text for a rasterized page; implementations may wrap pytesseract, cloud OCR, etc."""

    async def extract_pdf_text(self, pdf_path: Path) -> str:
        """Full-document OCR; default loops page indices for providers that only expose per-page APIs."""

        pieces: list[str] = []
        for page_index in range(100):
            snippet = await self.extract_pdf_page_text(pdf_path, page_index)
            if snippet.strip():
                pieces.append(snippet)
        return "\n".join(pieces)

    async def extract_image_text(self, image_path: Path, mime_type: str) -> str:  # noqa: ARG002
        """Raster OCR for contract scans; noop by default."""

        return ""


class StubOcrProvider(OcrProvider):
    """Production-safe noop — logs intent only; avoids shipping native tess dependencies in MVP."""

    async def extract_pdf_page_text(self, pdf_path: Path, page_index: int) -> str:  # noqa: ARG002
        return ""

    async def extract_pdf_text(self, pdf_path: Path) -> str:  # noqa: ARG002
        return ""

    async def extract_image_text(self, image_path: Path, mime_type: str) -> str:  # noqa: ARG002
        return ""
