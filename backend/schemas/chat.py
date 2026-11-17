"""对话 API 请求/响应模型。"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST /api/chat 请求体。"""

    question: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class CitationOut(BaseModel):
    """引用来源。"""

    source: str
    section: str


class ChatResponse(BaseModel):
    """POST /api/chat 响应体。"""

    message_id: str
    session_id: str
    answer: str
    citations: list[CitationOut]
    trace_id: str


class MessageOut(BaseModel):
    """单条消息。"""

    id: str
    role: str
    content: str
    created_at: str
    citations: list[CitationOut] = []


class SessionOut(BaseModel):
    """会话摘要。"""

    id: str
    title: str
    created_at: str
