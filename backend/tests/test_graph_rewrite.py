"""Phase 2：grade + rewrite 图路由测试。"""
from unittest.mock import MagicMock, patch

from backend.agent.graph import build_graph
from backend.runtime import load_runtime, reset_runtime_cache, save_runtime


def _mock_llm_sequence(contents: list[str]):
    """按调用顺序返回预设 LLM 文本。"""
    mock_llm = MagicMock()
    calls = {"i": 0}

    def invoke(_messages):
        idx = min(calls["i"], len(contents) - 1)
        calls["i"] += 1
        return MagicMock(content=contents[idx])

    mock_llm.invoke.side_effect = invoke
    return mock_llm


@patch("backend.agent.nodes.get_llm")
@patch("backend.agent.nodes.retrieve_with_scores")
def test_rewrite_then_generate(mock_retrieve, mock_llm):
    """第一次检索差、改写后检索好时，应出现 rewrite 并最终 generate。"""
    reset_runtime_cache()
    save_runtime({"max_rewrite_retries": 2, "enable_llm_grade": False})

    bad_doc = [{"source": "x.md", "section": "a", "content": "c", "score": 0.1, "distance": 600.0}]
    good_doc = [{"source": "wiki/billing.md", "section": "定价", "content": "99元", "score": 0.9, "distance": 80.0}]
    mock_retrieve.side_effect = [bad_doc, good_doc]

    mock_llm.return_value = _mock_llm_sequence(
        ['{"route": "need_rag"}', "企业版计费价格", "企业版按 99 元/月计费"]
    )

    graph = build_graph()
    result = graph.invoke({"question": "贵不贵啊", "chat_history": [], "node_trace": []})

    names = [n["name"] for n in result.get("node_trace", [])]
    assert "rewrite" in names
    assert "generate" in names
    assert result.get("answer")


@patch("backend.agent.nodes.get_llm")
@patch("backend.agent.nodes.retrieve_with_scores")
def test_rewrite_exhausted_refuses(mock_retrieve, mock_llm):
    """多次检索仍不相关时应拒答。"""
    reset_runtime_cache()
    save_runtime({"max_rewrite_retries": 1, "enable_llm_grade": False})

    far = [{"source": "x.md", "section": "a", "content": "c", "score": 0.1, "distance": 900.0}]
    mock_retrieve.return_value = far
    mock_llm.return_value = _mock_llm_sequence(['{"route": "need_rag"}', "火星登录方法"])

    graph = build_graph()
    result = graph.invoke({"question": "火星登录", "chat_history": [], "node_trace": []})

    assert load_runtime().refuse_message in result["answer"]
    names = [n["name"] for n in result.get("node_trace", [])]
    assert "rewrite" in names
    assert "refuse" in names or load_runtime().refuse_message in result["answer"]
