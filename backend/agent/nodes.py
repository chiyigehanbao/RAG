"""LangGraph 节点：classify, retrieve, grade, rewrite, generate, refuse, chitchat。"""
import json
import time

from langchain_core.messages import HumanMessage

from backend.agent.history import format_history_block
from backend.agent.llm import get_llm
from backend.agent.prompts import (
    CHITCHAT_PROMPT,
    CLASSIFY_PROMPT,
    GENERATE_PROMPT,
    GRADE_PROMPT,
    REWRITE_PROMPT,
)
from backend.agent.state import AgentState, NodeTrace
from backend.agent.text_format import plain_answer_text
from backend.rag.corpus import chroma_where, corpus_label, resolve_corpus
from backend.rag.retriever import retrieve_with_scores
from backend.runtime import load_runtime


def _append_trace(
    state: AgentState, name: str, duration_ms: int, inp: dict, out: dict
) -> list[NodeTrace]:
    """追加节点 trace 到 state。"""
    trace = list(state.get("node_trace") or [])
    trace.append({"name": name, "duration_ms": duration_ms, "input": inp, "output": out})
    return trace


def _history_text(state: AgentState) -> str:
    """从 state 取出并格式化多轮历史。"""
    return format_history_block(state.get("chat_history") or [])


def _min_distance(docs: list[dict]) -> float | None:
    """取检索结果中最小 L2 距离。"""
    distances = [float(d["distance"]) for d in docs if d.get("distance") is not None]
    if not distances:
        return None
    return min(distances)


def _snippet_text(docs: list[dict], limit: int = 3) -> str:
    """拼接若干 chunk 摘要供 grade LLM 使用。"""
    parts: list[str] = []
    for doc in docs[:limit]:
        content = str(doc.get("content", ""))[:200]
        parts.append(f"- [{doc.get('source')} § {doc.get('section')}] {content}")
    return "\n".join(parts) if parts else "（无）"


def evaluate_relevance(state: AgentState) -> tuple[bool, str]:
    """
    判断检索结果是否足以回答当前问题。
    返回 (is_relevant, grade_reason)。
    """
    runtime = load_runtime()
    docs = state.get("documents") or []
    if not docs:
        return False, "empty"

    min_dist = _min_distance(docs)
    threshold = runtime.max_retrieval_distance
    if min_dist is None:
        return True, "ok"
    if min_dist <= threshold:
        return True, "ok"
    if min_dist > threshold + runtime.grade_margin:
        return False, "distance"
    if not runtime.enable_llm_grade:
        return False, "distance"

    llm = get_llm()
    prompt = GRADE_PROMPT.format(
        product_name=runtime.product_name,
        question=state["question"],
        snippets=_snippet_text(docs),
    )
    raw = str(llm.invoke([HumanMessage(content=prompt)]).content).strip()
    try:
        parsed = json.loads(raw)
        relevant = bool(parsed.get("relevant", False))
    except json.JSONDecodeError:
        relevant = "true" in raw.lower() and "false" not in raw.lower()

    return (True, "llm") if relevant else (False, "llm_reject")


def should_refuse_after_retrieve(state: AgentState) -> bool:
    """兼容旧测试：无文档或距离过大视为不相关。"""
    relevant, _ = evaluate_relevance(state)
    return not relevant


def classify_node(state: AgentState) -> AgentState:
    """判断是否需要 RAG 检索。"""
    start = time.perf_counter()
    llm = get_llm()
    runtime = load_runtime()
    prompt = CLASSIFY_PROMPT.format(
        product_name=runtime.product_name,
        history=_history_text(state),
        question=state["question"],
    )
    raw = llm.invoke([HumanMessage(content=prompt)]).content

    route = "need_rag"
    corpus = "all"
    try:
        parsed = json.loads(str(raw).strip())
        route = parsed.get("route", "need_rag")
        if route == "need_rag":
            corpus = parsed.get("corpus", "all")
    except json.JSONDecodeError:
        route = "need_rag" if "no_rag" not in str(raw) else "no_rag"

    elapsed = int((time.perf_counter() - start) * 1000)
    trace_out: dict = {"route": route}
    if route == "need_rag":
        trace_out["corpus"] = corpus
    return {
        "route": route,
        "corpus": corpus,
        "node_trace": _append_trace(
            state, "classify", elapsed, {"question": state["question"]}, trace_out
        ),
    }


def retrieve_node(state: AgentState) -> AgentState:
    """向量检索 top-k chunks。"""
    start = time.perf_counter()
    runtime = load_runtime()
    query = state.get("rewritten_question") or state["question"]
    final_corpus = resolve_corpus(state.get("corpus"), runtime.retrieval_scope)
    where = chroma_where(final_corpus)
    docs = retrieve_with_scores(query, where=where)
    scores = [d["score"] for d in docs]
    distances = [d["distance"] for d in docs]
    elapsed = int((time.perf_counter() - start) * 1000)

    return {
        "documents": docs,
        "relevance_scores": scores,
        "retrieval_corpus": final_corpus.value,
        "node_trace": _append_trace(
            state,
            "retrieve",
            elapsed,
            {"query": query},
            {
                "top_k": len(docs),
                "chunks": docs,
                "min_distance": min(distances) if distances else None,
                "retrieval_scope_label": corpus_label(final_corpus),
            },
        ),
    }


def grade_node(state: AgentState) -> AgentState:
    """评估检索结果是否相关，决定 generate / rewrite / refuse。"""
    start = time.perf_counter()
    is_relevant, reason = evaluate_relevance(state)
    elapsed = int((time.perf_counter() - start) * 1000)
    min_dist = _min_distance(state.get("documents") or [])

    return {
        "is_relevant": is_relevant,
        "grade_reason": reason,
        "node_trace": _append_trace(
            state,
            "grade",
            elapsed,
            {"question": state["question"], "retry_count": state.get("retry_count") or 0},
            {
                "is_relevant": is_relevant,
                "grade_reason": reason,
                "min_distance": min_dist,
            },
        ),
    }


def rewrite_node(state: AgentState) -> AgentState:
    """改写检索 query 后回到 retrieve。"""
    start = time.perf_counter()
    runtime = load_runtime()
    llm = get_llm()
    last_query = state.get("rewritten_question") or state["question"]
    reason = state.get("grade_reason") or "distance"
    reason_text = {
        "empty": "未找到任何文档片段",
        "distance": "与文档相似度不足",
        "llm_reject": "资料与问题匹配度不足",
    }.get(reason, reason)

    prompt = REWRITE_PROMPT.format(
        product_name=runtime.product_name,
        history=_history_text(state),
        question=state["question"],
        last_query=last_query,
        reason=reason_text,
    )
    rewritten = str(llm.invoke([HumanMessage(content=prompt)]).content).strip()
    rewritten = rewritten.strip("\"'").split("\n")[0][:120]
    retry = (state.get("retry_count") or 0) + 1
    elapsed = int((time.perf_counter() - start) * 1000)

    return {
        "rewritten_question": rewritten,
        "retry_count": retry,
        "node_trace": _append_trace(
            state,
            "rewrite",
            elapsed,
            {"original_query": state["question"], "last_query": last_query},
            {"rewritten_query": rewritten, "retry_count": retry},
        ),
    }


def generate_node(state: AgentState) -> AgentState:
    """基于检索片段生成带引用答案。"""
    start = time.perf_counter()
    docs = state.get("documents") or []
    context = "\n\n---\n\n".join(
        f"[{d['source']} § {d['section']}]\n{d['content']}" for d in docs
    )
    llm = get_llm()
    runtime = load_runtime()
    prompt = GENERATE_PROMPT.format(
        product_name=runtime.product_name,
        history=_history_text(state),
        context=context,
        question=state["question"],
    )
    answer = plain_answer_text(str(llm.invoke([HumanMessage(content=prompt)]).content))

    citations = [{"source": d["source"], "section": d["section"]} for d in docs[:3]]
    elapsed = int((time.perf_counter() - start) * 1000)

    return {
        "answer": answer,
        "citations": citations,
        "node_trace": _append_trace(
            state,
            "generate",
            elapsed,
            {"context_chunks": len(docs)},
            {"answer_preview": answer[:120]},
        ),
    }


def refuse_node(state: AgentState) -> AgentState:
    """固定拒答话术（可在助手设定页修改）。"""
    return {
        "answer": load_runtime().refuse_message,
        "citations": [],
        "node_trace": state.get("node_trace") or [],
    }


def chitchat_node(state: AgentState) -> AgentState:
    """非知识库问题的简短回复。"""
    start = time.perf_counter()
    llm = get_llm()
    runtime = load_runtime()
    prompt = CHITCHAT_PROMPT.format(
        product_name=runtime.product_name,
        history=_history_text(state),
        question=state["question"],
    )
    answer = plain_answer_text(str(llm.invoke([HumanMessage(content=prompt)]).content))
    elapsed = int((time.perf_counter() - start) * 1000)

    return {
        "answer": answer,
        "citations": [],
        "node_trace": _append_trace(
            state,
            "chitchat",
            elapsed,
            {"question": state["question"]},
            {"answer_preview": answer[:80]},
        ),
    }
