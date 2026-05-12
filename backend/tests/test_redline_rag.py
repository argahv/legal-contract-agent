from __future__ import annotations

from uuid import uuid4

import pytest
from app.ai.chains.redline_chain import RedlineSuggestion, propose_redline_with_playbook
from app.core.config import get_settings
from app.models.playbook import PlaybookEntry


@pytest.mark.asyncio
async def test_redline_chain_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeStructured:
        def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
            pass

        def with_structured_output(self, _schema):  # noqa: ANN001
            return self

        def with_config(self, **_kwargs):  # noqa: ANN003
            return self

        async def ainvoke(self, _messages):  # noqa: ANN001
            return RedlineSuggestion(
                original="risky",
                suggested="safe",
                explanation="playbook alignment",
                playbook_ref=None,
            )

    monkeypatch.setattr("app.ai.chains.redline_chain.ChatOpenAI", _FakeStructured)

    settings = get_settings()
    playbook_id = uuid4()
    row = PlaybookEntry(
        id=playbook_id,
        title="demo",
        clause_type="limitation_of_liability",
        guideline="cap liability",
        preferred_language=None,
        embedding=None,
    )
    result = await propose_redline_with_playbook(
        settings=settings,
        clause_text="risky text",
        clause_type="limitation_of_liability",
        playbook_rows=[row],
        usage=None,
    )
    assert result.suggested == "safe"
    assert result.playbook_ref is None
