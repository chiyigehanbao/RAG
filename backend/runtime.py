"""运行时助手设定：前端可改、覆盖 .env 默认值，持久化到 JSON。"""
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from backend.config import get_settings

_SETTINGS_FILE = Path("./data/runtime_settings.json")


class RuntimeSettings(BaseModel):
    """可在前端「助手设定」页修改的项（不含密钥）。"""

    product_name: str = Field(default="RAG 架构助手", description="产品中文名，用于 Prompt 与界面")
    retrieve_top_k: int = Field(default=10, ge=1, le=30)
    max_retrieval_distance: float = Field(default=450.0, ge=50.0, le=800.0)
    refuse_message: str = Field(
        default="暂未在知识库中找到相关资料，建议联系管理员或提交工单。",
        max_length=500,
    )
    max_rewrite_retries: int = Field(default=2, ge=0, le=3)
    enable_llm_grade: bool = Field(default=True)
    grade_margin: float = Field(default=80.0, ge=0.0, le=200.0)
    retrieval_scope: str = Field(
        default="auto",
        description="检索范围：auto|all|arch_only|business_only",
    )


_cache: RuntimeSettings | None = None


def _defaults() -> RuntimeSettings:
    """以 .env 为底，填充未持久化的字段。"""
    env = get_settings()
    return RuntimeSettings(
        product_name="RAG 架构助手",
        retrieve_top_k=env.retrieve_top_k,
        max_retrieval_distance=env.max_retrieval_distance,
    )


def load_runtime() -> RuntimeSettings:
    """加载运行时设定（内存缓存 + 文件）。"""
    global _cache
    if _cache is not None:
        return _cache

    base = _defaults()
    if not _SETTINGS_FILE.exists():
        _cache = base
        return _cache

    try:
        raw = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
        _cache = RuntimeSettings.model_validate({**base.model_dump(), **raw})
    except (json.JSONDecodeError, OSError, ValueError):
        _cache = base

    return _cache


def save_runtime(patch: dict[str, Any]) -> RuntimeSettings:
    """合并更新并写入文件。"""
    global _cache
    current = load_runtime()
    merged = current.model_copy(update={k: v for k, v in patch.items() if v is not None})
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(
        json.dumps(merged.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _cache = merged
    return _cache


def reset_runtime_cache() -> None:
    """测试用：清空内存缓存。"""
    global _cache
    _cache = None
