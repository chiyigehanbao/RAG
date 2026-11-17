"""Ollama Embedding 封装，供 Chroma 与 Retriever 使用。"""
from functools import lru_cache

from langchain_community.embeddings import OllamaEmbeddings

from backend.config import get_settings


@lru_cache
def get_embedding_function() -> OllamaEmbeddings:
    """
    返回缓存的 Ollama Embedding 客户端。

    Returns:
        配置好 model 与 base_url 的 OllamaEmbeddings 实例
    """
    settings = get_settings()
    return OllamaEmbeddings(
        model=settings.ollama_embedding_model,
        base_url=settings.ollama_base_url,
    )
