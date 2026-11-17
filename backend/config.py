"""应用配置：从环境变量加载 DeepSeek、Ollama、Chroma、SQLite 等参数。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置项。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8-sig",  # 兼容 Windows 记事本保存的 BOM
    )

    # DeepSeek — 对话与 Agent 推理
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # Ollama — 本地 Embedding（nomic-embed-text）
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"

    # 存储路径
    chroma_persist_dir: str = "./data/chroma"
    sqlite_url: str = "sqlite:///./db/novacloud.db"

    # RAG 检索
    retrieve_top_k: int = 10
    relevance_threshold: float = 0.5  # 保留兼容，拒答改用 max_retrieval_distance
    max_retrieval_distance: float = 450.0  # Chroma L2 距离上限，越小越相似

    # CORS
    cors_origins: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    """返回缓存的配置单例。"""
    return Settings()
