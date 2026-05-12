"""Tests for raster image loading via OCR seam in `load_text_from_path`."""

from __future__ import annotations

import pytest

from app.ai.ingestion.loaders import load_text_from_path


@pytest.mark.asyncio
async def test_load_text_from_path_image_uses_stub_ocr_empty_string(tmp_path) -> None:
    """StubOcrProvider returns empty OCR text for images (same contract as PDF stub)."""

    image_path = tmp_path / "page.jpg"
    image_path.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF")
    text = await load_text_from_path(
        storage_path=str(image_path),
        mime_type="image/jpeg",
    )
    assert text == ""
