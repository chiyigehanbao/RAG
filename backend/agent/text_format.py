"""助手回复纯文本化（前端不渲染 Markdown）。"""
import re


def plain_answer_text(text: str) -> str:
    """去掉常见 Markdown 标记，保留可读正文。"""
    out = str(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"\1", out)
    out = re.sub(r"__(.+?)__", r"\1", out)
    out = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", out)
    out = re.sub(r"`([^`]+)`", r"\1", out)
    return out
