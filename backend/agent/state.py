"""LangGraph AgentState 类型定义。"""
from typing import TypedDict


class Citation(TypedDict):
    """引用来源。"""

    source: str
    section: str


class NodeTrace(TypedDict, total=False):
    """单节点调试 trace。"""

    name: str
    duration_ms: int
    input: dict
    output: dict


class AgentState(TypedDict, total=False):
    """图状态：在各节点间传递。"""

    question: str
    chat_history: list[dict]
    rewritten_question: str | None
    route: str
    corpus: str
    retrieval_corpus: str
    documents: list[dict]
    relevance_scores: list[float]
    retry_count: int
    is_relevant: bool
    grade_reason: str | None
    answer: str
    citations: list[Citation]
    node_trace: list[NodeTrace]
