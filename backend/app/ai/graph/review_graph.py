"""LangGraph orchestration — ingest/extract node then clause analysis node."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict
from uuid import UUID

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph

if TYPE_CHECKING:
    from app.ai.chains.agent import LegalReviewAgent


class ReviewGraphState(TypedDict, total=False):
    extraction: dict[str, Any]


async def _node_ingest(state: ReviewGraphState, config: RunnableConfig) -> ReviewGraphState:
    _ = state
    agent: LegalReviewAgent = config["configurable"]["agent"]  # type: ignore[assignment]
    usage = config["configurable"]["usage"]
    progress = config["configurable"]["progress"]
    trace_meta = config["configurable"]["trace_meta"]
    document = config["configurable"]["document"]
    document_id = UUID(config["configurable"]["document_id"])
    actor_id = UUID(config["configurable"]["actor_id"])
    extraction = await agent._run_pipeline_and_extract(
        document, document_id, actor_id, usage, progress, trace_meta
    )
    return {"extraction": extraction.model_dump(mode="json")}


async def _node_clauses(state: ReviewGraphState, config: RunnableConfig) -> ReviewGraphState:
    from app.ai.chains.extraction import ExtractionResult

    agent: LegalReviewAgent = config["configurable"]["agent"]  # type: ignore[assignment]
    usage = config["configurable"]["usage"]
    progress = config["configurable"]["progress"]
    trace_meta = config["configurable"]["trace_meta"]
    document = config["configurable"]["document"]
    actor_id = UUID(config["configurable"]["actor_id"])
    extraction = ExtractionResult.model_validate(state["extraction"])
    await agent._run_clause_loop(
        document, extraction, actor_id, usage, progress, trace_meta
    )
    return {}


def build_review_graph() -> Any:
    graph = StateGraph(ReviewGraphState)
    graph.add_node("ingest", _node_ingest)  # type: ignore[arg-type]
    graph.add_node("clauses", _node_clauses)  # type: ignore[arg-type]
    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "clauses")
    graph.add_edge("clauses", END)
    return graph.compile()


async def invoke_review_graph(
    agent: LegalReviewAgent,
    *,
    document: Any,
    document_id: UUID,
    actor_id: UUID,
    usage: Any,
    progress: Any,
    trace_meta: dict[str, str],
) -> None:
    graph = build_review_graph()
    # LangGraph requires the input to touch at least one state key; `{}` raises
    # InvalidUpdateError: Must write to at least one of ['extraction'] on __start__.
    initial: ReviewGraphState = {"extraction": {"clauses": []}}
    await graph.ainvoke(
        initial,
        config={
            "configurable": {
                "agent": agent,
                "document": document,
                "document_id": str(document_id),
                "actor_id": str(actor_id),
                "usage": usage,
                "progress": progress,
                "trace_meta": trace_meta,
            }
        },
    )
