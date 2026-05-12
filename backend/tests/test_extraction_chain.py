from __future__ import annotations

import pytest
from app.ai.chains.extraction import ExtractedClause, ExtractionResult
from app.ai.chains.extraction_chain import extract_clauses_chunked
from app.core.config import get_settings
from app.models.enums import ClauseType


@pytest.mark.asyncio
async def test_extraction_chunked_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeStructured:
        def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            pass

        def with_structured_output(self, _schema):  # noqa: ANN001
            return self

        def with_config(self, **_kwargs):  # noqa: ANN003
            return self

        async def ainvoke(self, _messages):  # noqa: ANN001
            return ExtractionResult(
                clauses=[
                    ExtractedClause(
                        title="LoL",
                        clause_type="limitation_of_liability",
                        body="Liability capped at fees paid.",
                        confidence=0.9,
                    )
                ],
            )

    monkeypatch.setattr("app.ai.chains.extraction_chain.ChatOpenAI", _FakeStructured)

    settings = get_settings()
    result = await extract_clauses_chunked(settings=settings, contract_text="chunk text", usage=None)
    assert len(result.clauses) == 1
    assert result.clauses[0].clause_type == ClauseType.LIMITATION_OF_LIABILITY
