"""LangGraph 节点测试。"""
from backend.agent.nodes import refuse_node, should_refuse_after_retrieve
from backend.runtime import load_runtime


def test_should_refuse_when_no_docs():
    """无检索结果时应拒答。"""
    state = {"documents": [], "relevance_scores": []}
    assert should_refuse_after_retrieve(state) is True


def test_should_not_refuse_when_distance_ok():
    """L2 距离在阈值内时不拒答。"""
    state = {"documents": [{"distance": 320.0}]}
    assert should_refuse_after_retrieve(state) is False


def test_refuse_node_sets_message():
    """拒答节点应写入固定话术。"""
    result = refuse_node({"question": "火星怎么登录"})
    assert result["answer"] == load_runtime().refuse_message
