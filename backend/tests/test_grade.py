"""grade 节点逻辑测试。"""
from unittest.mock import patch

from backend.agent.nodes import evaluate_relevance, grade_node
from backend.runtime import reset_runtime_cache, save_runtime


def test_evaluate_empty_docs():
    """无文档时不相关。"""
    state = {"question": "q", "documents": []}
    ok, reason = evaluate_relevance(state)
    assert ok is False
    assert reason == "empty"


def test_evaluate_distance_ok():
    """距离在阈值内时相关。"""
    reset_runtime_cache()
    save_runtime({"max_retrieval_distance": 450.0, "enable_llm_grade": False})
    state = {"question": "计费", "documents": [{"distance": 200.0, "content": "x", "source": "a", "section": "b"}]}
    ok, reason = evaluate_relevance(state)
    assert ok is True
    assert reason == "ok"


def test_evaluate_distance_too_far():
    """距离远超阈值时不相关。"""
    reset_runtime_cache()
    save_runtime({"max_retrieval_distance": 450.0, "grade_margin": 80.0, "enable_llm_grade": False})
    state = {"question": "q", "documents": [{"distance": 900.0, "content": "x", "source": "a", "section": "b"}]}
    ok, reason = evaluate_relevance(state)
    assert ok is False
    assert reason == "distance"


@patch("backend.agent.nodes.get_llm")
def test_grade_node_trace(mock_llm):
    """grade_node 应写入 trace。"""
    reset_runtime_cache()
    save_runtime({"enable_llm_grade": False})
    state = {"question": "q", "documents": [{"distance": 100.0, "content": "c", "source": "f", "section": "s"}]}
    out = grade_node({**state, "node_trace": []})
    assert out["is_relevant"] is True
    assert any(n["name"] == "grade" for n in out["node_trace"])
