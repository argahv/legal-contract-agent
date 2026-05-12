"""Unit tests for Google Document AI OCR provider."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.ai.ocr_google_docai import GoogleDocumentAIOcrProvider
from app.core.config import Settings, reset_settings_cache


@pytest.fixture(autouse=True)
def _settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/t")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setenv("GOOGLE_DOCAI_PROJECT_ID", "test-project")
    monkeypatch.setenv("GOOGLE_DOCAI_PROCESSOR_ID", "processor-id-abc")
    monkeypatch.setenv("GOOGLE_DOCAI_LOCATION", "us")


@pytest.fixture
def docai_settings() -> Settings:
    reset_settings_cache()
    try:
        return Settings()
    finally:
        reset_settings_cache()


@pytest.mark.asyncio
async def test_google_document_ai_extract_pdf_text_uses_full_pdf_bytes(
    tmp_path,
    docai_settings: Settings,
) -> None:
    pdf_path = tmp_path / "scan.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 minimal")

    mock_client = MagicMock()
    mock_client.processor_path.return_value = (
        "projects/test-project/locations/us/processors/processor-id-abc"
    )
    proc_result = MagicMock()
    proc_result.document.text = "Full doc OCR text\n"
    mock_client.process_document.return_value = proc_result

    with patch(
        "app.ai.ocr_google_docai.documentai.DocumentProcessorServiceClient",
        return_value=mock_client,
    ):
        provider = GoogleDocumentAIOcrProvider(docai_settings)
        text = await provider.extract_pdf_text(pdf_path)

    assert text == "Full doc OCR text"

    mock_client.processor_path.assert_called_once_with(
        "test-project",
        "us",
        "processor-id-abc",
    )
    mock_client.process_document.assert_called_once()
    req = mock_client.process_document.call_args.kwargs["request"]
    assert req.raw_document.content == b"%PDF-1.4 minimal"
    assert req.raw_document.mime_type == "application/pdf"
    assert req.name == mock_client.processor_path.return_value


@pytest.mark.asyncio
async def test_google_document_ai_extract_image_text_uses_bytes_and_mime(
    tmp_path,
    docai_settings: Settings,
) -> None:
    img_path = tmp_path / "page.jpeg"
    img_path.write_bytes(b"\xff\xd8\xff fake jpeg bytes")

    mock_client = MagicMock()
    mock_client.processor_path.return_value = (
        "projects/test-project/locations/us/processors/processor-id-abc"
    )
    proc_result = MagicMock()
    proc_result.document.text = "Clause from scan\n"
    mock_client.process_document.return_value = proc_result

    with patch(
        "app.ai.ocr_google_docai.documentai.DocumentProcessorServiceClient",
        return_value=mock_client,
    ):
        provider = GoogleDocumentAIOcrProvider(docai_settings)
        text = await provider.extract_image_text(img_path, "image/jpeg")

    assert text == "Clause from scan"

    req = mock_client.process_document.call_args.kwargs["request"]
    assert req.raw_document.content == b"\xff\xd8\xff fake jpeg bytes"
    assert req.raw_document.mime_type == "image/jpeg"


def test_google_document_ai_init_raises_when_project_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_DOCAI_PROJECT_ID", raising=False)
    reset_settings_cache()
    try:
        # Skip dotenv so a repo `.env` cannot repopulate the deleted OS variable.
        settings = Settings(_env_file=None)
        with pytest.raises(ValueError, match="google_docai_project_id"):
            GoogleDocumentAIOcrProvider(settings)
    finally:
        reset_settings_cache()


@pytest.mark.asyncio
async def test_google_document_ai_page_extract_not_implemented(docai_settings: Settings) -> None:
    provider = GoogleDocumentAIOcrProvider(docai_settings)
    with pytest.raises(NotImplementedError):
        await provider.extract_pdf_page_text(Path("/tmp/not-used.pdf"), 0)
