"""助手设定 API 模型。"""
from pydantic import BaseModel, Field


class SettingsOut(BaseModel):
    """返回给前端的可编辑设定。"""

    product_name: str
    retrieve_top_k: int
    max_retrieval_distance: float
    refuse_message: str
    max_rewrite_retries: int
    enable_llm_grade: bool
    grade_margin: float
    retrieval_scope: str


class SettingsUpdate(BaseModel):
    """部分更新助手设定。"""

    product_name: str | None = Field(default=None, min_length=1, max_length=32)
    retrieve_top_k: int | None = Field(default=None, ge=1, le=30)
    max_retrieval_distance: float | None = Field(default=None, ge=50.0, le=800.0)
    refuse_message: str | None = Field(default=None, min_length=1, max_length=500)
    max_rewrite_retries: int | None = Field(default=None, ge=0, le=3)
    enable_llm_grade: bool | None = None
    grade_margin: float | None = Field(default=None, ge=0.0, le=200.0)
    retrieval_scope: str | None = Field(
        default=None,
        pattern="^(auto|all|arch_only|business_only)$",
    )
