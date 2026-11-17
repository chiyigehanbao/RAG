"""LangGraph 流式执行：推送节点事件与答案 token。"""
from collections.abc import Generator
from typing import Any

from backend.agent.graph import build_graph
from backend.agent.history import HistoryMessage
from backend.agent.state import AgentState


def _format_node_event(trace_entry: dict) -> dict[str, Any]:
    """将 node_trace 单条转为 SSE 负载。"""
    name = trace_entry.get("name", "unknown")
    output = trace_entry.get("output") or {}
    detail: dict[str, Any] = {}

    if name == "classify":
        detail["route"] = output.get("route")
    elif name == "retrieve":
        detail["top_k"] = output.get("top_k")
        detail["min_distance"] = output.get("min_distance")
    elif name == "grade":
        detail["is_relevant"] = output.get("is_relevant")
        detail["grade_reason"] = output.get("grade_reason")
        detail["min_distance"] = output.get("min_distance")
    elif name == "rewrite":
        inp = trace_entry.get("input") or {}
        detail["rewritten_query"] = output.get("rewritten_query")
        detail["retry_count"] = output.get("retry_count")
        detail["last_query"] = inp.get("last_query") or inp.get("original_query")
    elif name in {"generate", "chitchat"}:
        detail["answer_preview"] = output.get("answer_preview")

    return {
        "type": "node",
        "name": name,
        "duration_ms": trace_entry.get("duration_ms", 0),
        "detail": detail,
    }


def stream_agent(
    question: str,
    chat_history: list[HistoryMessage] | None = None,
) -> Generator[dict[str, Any], None, None]:
    """
    流式执行 Agent，依次 yield node / token / done / error 事件。
    """
    graph = build_graph()
    initial: AgentState = {
        "question": question,
        "chat_history": chat_history or [],
        "node_trace": [],
    }
    emitted_traces = 0
    final_state: AgentState = dict(initial)

    try:
        for event in graph.stream(initial, stream_mode="updates"):
            for _node_name, partial in event.items():
                if not partial:
                    continue
                final_state.update(partial)

                trace_list = partial.get("node_trace") or []
                if len(trace_list) > emitted_traces:
                    for entry in trace_list[emitted_traces:]:
                        yield _format_node_event(entry)
                    emitted_traces = len(trace_list)

        answer = str(final_state.get("answer") or "")
        if answer:
            chunk_size = 6
            for i in range(0, len(answer), chunk_size):
                yield {"type": "token", "content": answer[i : i + chunk_size]}

        yield {
            "type": "done",
            "answer": answer,
            "citations": final_state.get("citations") or [],
            "node_trace": final_state.get("node_trace") or [],
        }
    except Exception as exc:
        yield {"type": "error", "message": str(exc)}
