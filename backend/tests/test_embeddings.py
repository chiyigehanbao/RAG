"""Embedding 模块测试。"""
from unittest.mock import MagicMock, patch

from backend.rag.embeddings import get_embedding_function


@patch("backend.rag.embeddings.OllamaEmbeddings")
def test_get_embedding_function_uses_ollama(mock_cls):
    """应返回 OllamaEmbeddings 实例并传入 nomic 模型。"""
    get_embedding_function.cache_clear()
    mock_cls.return_value = MagicMock()
    emb = get_embedding_function()
    assert emb is not None
    mock_cls.assert_called_once()
    kwargs = mock_cls.call_args.kwargs
    assert kwargs["model"] == "nomic-embed-text"
