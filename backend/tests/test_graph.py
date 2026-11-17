"""LangGraph 端到端测试。"""
from unittest.mock import patch

from backend.agent.graph import build_graph
from backend.runtime import load_runtime


@patch("backend.agent.nodes.get_llm")
@patch("backend.agent.nodes.retrieve_with_scores")
def test_graph_refuses_when_no_results(mock_retrieve, mock_llm):
    """无检索结果时应走 refuse 分支。"""
    mock_retrieve.return_value = []
    mock_llm.return_value.invoke.return_value.content = (
        '{"route": "need_rag", "corpus": "all"}'
    )

    graph = build_graph()
    result = graph.invoke({"question": "不存在的问题 xyz123"})

    assert load_runtime().refuse_message in result["answer"]
