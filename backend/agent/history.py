"""多轮对话历史：截断与 Prompt 格式化。"""
from typing import TypedDict

# 送入 LLM 的最近轮数（每轮 = 用户 + 助手各一条）
MAX_HISTORY_TURNS = 6


class HistoryMessage(TypedDict):
    """单条历史消息。"""

    role: str
    content: str


def trim_history(messages: list[HistoryMessage], max_turns: int = MAX_HISTORY_TURNS) -> list[HistoryMessage]:
    """保留最近 max_turns 轮，避免 Prompt 过长。"""
    if not messages:
        return []
    max_messages = max_turns * 2
    return messages[-max_messages:]


def format_history_block(messages: list[HistoryMessage]) -> str:
    """将历史格式化为 Prompt 中的文本块。"""
    trimmed = trim_history(messages)
    if not trimmed:
        return "（无此前对话）"

    lines: list[str] = []
    for msg in trimmed:
        label = "用户" if msg["role"] == "user" else "助手"
        content = msg["content"].strip().replace("\n", " ")
        if len(content) > 400:
            content = content[:400] + "…"
        lines.append(f"{label}：{content}")
    return "\n".join(lines)
