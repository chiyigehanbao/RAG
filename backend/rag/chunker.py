"""Markdown 按标题与 FAQ 问答题分块。"""
import re

from langchain_core.documents import Document

_MAX_SECTION_CHARS = 800
_OVERLAP_CHARS = 100
_MIN_SPLIT_CHARS = 400


def _split_faq_pairs(body: str, source: str, section: str) -> list[Document]:
    """
    将「问：… 答：…」格式的文本拆成独立 chunk。

    Args:
        body: 段落正文
        source: 文件路径
        section: 章节名

    Returns:
        FAQ 块列表
    """
    chunks: list[Document] = []
    blocks = re.split(r"(?m)(?=^问：)", body.strip())

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 15:
            continue

        question_line = block.split("\n", 1)[0].strip()
        faq_section = section
        if question_line.startswith("问："):
            faq_section = f"{section} · {question_line[2:].strip()[:24]}"

        chunks.append(
            Document(
                page_content=block,
                metadata={"source": source, "section": faq_section},
            )
        )

    return chunks


def _split_body_with_overlap(body: str, source: str, section: str) -> list[Document]:
    """长节正文按最大块长切分，相邻块 overlap。"""
    if len(body) <= _MIN_SPLIT_CHARS:
        content = f"## {section}\n\n{body}" if body else f"## {section}"
        return [
            Document(
                page_content=content,
                metadata={"source": source, "section": section},
            )
        ]

    chunks: list[Document] = []
    step = _MAX_SECTION_CHARS - _OVERLAP_CHARS
    start = 0
    while start < len(body):
        piece = body[start : start + _MAX_SECTION_CHARS]
        if not piece:
            break
        content = f"## {section}\n\n{piece}"
        chunks.append(
            Document(
                page_content=content,
                metadata={"source": source, "section": section},
            )
        )
        if start + _MAX_SECTION_CHARS >= len(body):
            break
        start += step
    return chunks


def split_markdown(text: str, source: str) -> list[Document]:
    """
    按 ## 二级标题切分；段首前言与 FAQ 问答题进一步拆分。

    Args:
        text: 原始 Markdown
        source: 文件相对路径

    Returns:
        带 source/section 元数据的 Document 列表
    """
    parts = re.split(r"(?m)^## ", text.strip())
    chunks: list[Document] = []

    preamble = parts[0].strip() if parts else ""
    if preamble:
        lines = preamble.split("\n")
        if lines and lines[0].startswith("# "):
            preamble = "\n".join(lines[1:]).strip()
        if preamble:
            chunks.extend(_split_faq_pairs(preamble, source, "概要"))

    for part in parts[1:]:
        part = part.strip()
        if not part:
            continue

        lines = part.split("\n", 1)
        section = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        if "问：" in body:
            chunks.extend(_split_faq_pairs(body, source, section))
            continue

        if not body and len(section) < 20:
            continue

        chunks.extend(_split_body_with_overlap(body, source, section))

    return chunks
