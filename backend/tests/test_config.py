"""配置模块测试。"""
from backend.config import get_settings


def test_settings_loads_defaults(monkeypatch):
    """显式 env 覆盖 .env 文件，验证默认值。"""
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")
    monkeypatch.setenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    monkeypatch.setenv("RETRIEVE_TOP_K", "10")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.deepseek_model == "deepseek-chat"
    assert settings.ollama_embedding_model == "nomic-embed-text"
    assert settings.retrieve_top_k == 10
