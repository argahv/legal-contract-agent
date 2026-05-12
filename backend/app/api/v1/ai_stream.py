"""Streaming LLM responses (SSE) — narrative probe; not a substitute for structured pipeline output."""

from __future__ import annotations

import json
from typing import Annotated
from app.api.deps import get_current_user, settings_dep
from app.core.config import Settings
from app.models.user import User
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

router = APIRouter()


class StreamClauseNarrativeBody(BaseModel):
    clause_type: str = Field(min_length=2, max_length=64)
    body: str = Field(min_length=20, description="Clause text to narrate risk themes for.")


@router.post("/stream/clause-narrative")
async def stream_clause_narrative(
    payload: StreamClauseNarrativeBody,
    _user: Annotated[User, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(settings_dep)],
):
    llm = ChatOpenAI(
        **chat_openai_kwargs(settings, temperature=0.2),
        streaming=True,
    )
    sys = SystemMessage(
        content=(
            "You are commercial counsel. Stream a concise narrative (no JSON) "
            "highlighting risk themes for the clause. Ground claims in quoted language."
        )
    )
    human = HumanMessage(
        content=f"CLAUSE_TYPE: {payload.clause_type}\nCLAUSE:\n{payload.body}",
    )

    async def token_gen():
        async for chunk in llm.astream([sys, human]):
            text = getattr(chunk, "content", None) or ""
            if text:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        token_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
