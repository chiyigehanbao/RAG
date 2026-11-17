"""DeepSeek LLM 客户端（OpenAI 兼容接口）。"""
from functools import lru_cache

from langchain_openai import ChatOpenAI

from backend.config import get_settings


@lru_cache
def get_llm() -> ChatOpenAI:
    """返回 DeepSeek ChatOpenAI 实例。"""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.2,
    )
