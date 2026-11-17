"""LLM 客户端测试。"""
from unittest.mock import patch

from backend.agent.llm import get_llm


@patch("backend.agent.llm.ChatOpenAI")
def test_get_llm_uses_deepseek_config(mock_chat):
    """LLM 应使用 DeepSeek base_url 与 model。"""
    get_llm.cache_clear()
    get_llm()
    mock_chat.assert_called_once()
    kwargs = mock_chat.call_args.kwargs
    assert "deepseek" in kwargs["base_url"] or kwargs["model"] == "deepseek-chat"
