"""编译 LangGraph StateGraph（Phase 2：含 grade + rewrite）。"""
from langgraph.graph import END, StateGraph

from backend.agent.nodes import (
    chitchat_node,
    classify_node,
    generate_node,
    grade_node,
    refuse_node,
    retrieve_node,
    rewrite_node,
)
from backend.agent.state import AgentState
from backend.runtime import load_runtime


def _route_after_classify(state: AgentState) -> str:
    """classify 后路由。"""
    if state.get("route") == "no_rag":
        return "chitchat"
    return "retrieve"


def _route_after_grade(state: AgentState) -> str:
    """grade 后：生成、改写或拒答。"""
    if state.get("is_relevant"):
        return "generate"

    retry = state.get("retry_count") or 0
    if retry < load_runtime().max_rewrite_retries:
        return "rewrite"
    return "refuse"


def build_graph():
    """构建并编译 Agent 图。"""
    graph = StateGraph(AgentState)

    graph.add_node("classify", classify_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("grade", grade_node)
    graph.add_node("rewrite", rewrite_node)
    graph.add_node("generate", generate_node)
    graph.add_node("refuse", refuse_node)
    graph.add_node("chitchat", chitchat_node)

    graph.set_entry_point("classify")
    graph.add_conditional_edges(
        "classify",
        _route_after_classify,
        {"retrieve": "retrieve", "chitchat": "chitchat"},
    )
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges(
        "grade",
        _route_after_grade,
        {"generate": "generate", "rewrite": "rewrite", "refuse": "refuse"},
    )
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("generate", END)
    graph.add_edge("refuse", END)
    graph.add_edge("chitchat", END)

    return graph.compile()
