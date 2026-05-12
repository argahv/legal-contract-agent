"""Optional bounded ReAct-style playbook search before structured risk output."""

from __future__ import annotations

from typing import Any

from app.ai.chains.risk import LlmRiskJudgment, build_risk_chain
from app.ai.llm_usage import LLMUsageRecorder
from app.ai.openai_compatible import chat_openai_kwargs
from app.ai.openai_retry import openai_retry
from app.ai.vector_store import PlaybookVectorStore
from app.core.config import Settings
from app.core.logging_setup import get_logger
from app.models.enums import RiskLevel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

LOG = get_logger(__name__)

_MAX_TOOL_ROUNDS = 3


def _make_playbook_tool(
    *,
    store: PlaybookVectorStore,
    embedding: list[float],
    clause_type: str,
    clause_body: str,
) -> StructuredTool:
    async def _search(extra_query: str = "") -> str:
        """Retrieve top playbook rows; pass extra legal phrases to widen recall."""
        q = f"{extra_query}\n{clause_body}" if extra_query else clause_body
        rows = await store.similar_playbook_entries_for_clause_type(
            query_embedding=embedding,
            clause_type=clause_type,
            clause_body=q,
            k=4,
        )
        if not rows:
            return "(no playbook rows)"
        parts = []
        for r in rows:
            parts.append(f"[{r.id}] {r.title}:\n{r.guideline[:1200]}")
        return "\n\n---\n\n".join(parts)

    return StructuredTool.from_function(
        name="search_playbook",
        description="Search internal legal playbook for clauses similar to this risk. Optional extra_query adds keywords.",
        coroutine=_search,
    )


@openai_retry
async def llm_assess_clause_react(
    *,
    settings: Settings,
    session: AsyncSession,
    clause_title: str | None,
    clause_type: str,
    body: str,
    rule_level: RiskLevel | None,
    rule_hits: list[str],
    embedding: list[float],
    store: PlaybookVectorStore,
    usage: LLMUsageRecorder | None = None,
    trace_metadata: dict[str, str] | None = None,
) -> tuple[LlmRiskJudgment, dict[str, int]]:
    playbook_tool = _make_playbook_tool(
        store=store, embedding=embedding, clause_type=clause_type, clause_body=body
    )
    explorer = ChatOpenAI(**chat_openai_kwargs(settings, temperature=0.0)).bind_tools(
        [playbook_tool]
    )
    system = SystemMessage(
        content=(
            "You are an experienced commercial counsel. Use search_playbook at most twice "
            "to gather company playbook evidence; your next stage will convert findings to structured JSON."
        )
    )
    human = HumanMessage(
        content=(
            f"CLAUSE_TYPE: {clause_type}\n"
            f"TITLE: {clause_title}\n"
            f"RULE_LEVEL: {rule_level.value if rule_level else 'none'}\n"
            f"RULE_HITS: {', '.join(rule_hits) or 'none'}\n"
            f"CLAUSE BODY:\n{body}\n\n"
            "Call search_playbook if you need playbook context; otherwise reply briefly."
        )
    )
    messages: list[Any] = [system, human]
    rounds = 0
    while rounds < _MAX_TOOL_ROUNDS:
        ai: AIMessage = await explorer.ainvoke(
            messages,
            config={
                "run_name": "risk_react_explore",
                "tags": ["risk", "react", settings.app_name],
                "metadata": trace_metadata or {},
            },
        )
        messages.append(ai)
        if not ai.tool_calls:
            break
        for tc in ai.tool_calls:
            name = tc.get("name")
            tid = str(tc.get("id") or "call")
            if name != "search_playbook":
                messages.append(ToolMessage(content="unknown tool", tool_call_id=tid))
                continue
            args = tc.get("args") if isinstance(tc.get("args"), dict) else {}
            extra = str(args.get("extra_query", "") or "") if args else ""
            tool_result = await playbook_tool.ainvoke({"extra_query": extra})
            messages.append(ToolMessage(content=str(tool_result), tool_call_id=tid))
        rounds += 1

    hint_block = ""
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            hint_block = str(msg.content)
            break

    chain = build_risk_chain(settings).with_config(
        run_name="risk_assess_clause_react_final",
        tags=["risk", settings.app_name],
        metadata=trace_metadata or {},
    )
    final_human = HumanMessage(
        content=(
            f"CLAUSE_TYPE: {clause_type}\n"
            f"TITLE: {clause_title}\n"
            f"RULE_LEVEL: {rule_level.value if rule_level else 'none'}\n"
            f"RULE_HITS: {', '.join(rule_hits) or 'none'}\n"
            f"PLAYBOOK_HINT:\n{hint_block or 'n/a'}\n"
            f"CLAUSE BODY:\n{body}"
        ),
    )
    final_sys = SystemMessage(
        content=(
            "You are an experienced commercial counsel. Combine rule hits with contract text. "
            "Escalate risk when indemnity is uncapped, liability caps missing, or data breach exposure unclear. "
            "Always ground the explanation in concrete language from the clause."
        ),
    )
    judgment: LlmRiskJudgment = await chain.ainvoke([final_sys, final_human])
    if usage is not None:
        await usage.record(
            operation="risk.llm_assess_clause_react",
            model=settings.openai_model,
            input_units=len(body),
            output_units=len(judgment.explanation),
            vendor_metadata={"clause_type": clause_type, "rounds": rounds},
        )
    LOG.info("risk_react_complete", level=judgment.level, rounds=rounds)

    from app.ai.risk_cache import put_cached_risk_judgment, risk_judgment_cache_key

    if settings.risk_judgment_cache_enabled:
        key = risk_judgment_cache_key(
            settings=settings,
            clause_type=clause_type,
            body=body,
            rule_level=rule_level,
            rule_hits=rule_hits,
            playbook_excerpt=hint_block[:2000] if hint_block else None,
        )
        await put_cached_risk_judgment(
            session,
            key_hash=key,
            settings=settings,
            judgment=judgment,
        )

    return judgment, {"react_rounds": rounds}
