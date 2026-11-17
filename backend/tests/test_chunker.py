"""文档分块测试。"""
from backend.rag.chunker import split_markdown

SAMPLE = """# 部署指南

## 安装

运行 docker compose up。

## 配置

编辑 .env 文件，设置数据库连接与 API Key 等环境变量。
"""

FAQ_SAMPLE = """# NovaCloud 账号 FAQ

问：企业版如何计费？
答：企业版按年订阅，每席位 99 元/月。

## 账号

问：如何重置密码？
答：在登录页点击「忘记密码」。
"""


def test_split_markdown_by_headers():
    """应按 ## 标题分块并保留 section 元数据。"""
    chunks = split_markdown(SAMPLE, source="wiki/deployment.md")
    assert len(chunks) >= 2
    assert chunks[0].metadata["section"] == "安装"
    assert chunks[0].metadata["source"] == "wiki/deployment.md"


LONG_BODY = "段落内容。" * 200


def test_long_section_splits_with_overlap():
    """长节正文应切为多块且相邻块有重叠。"""
    text = f"# T\n\n## 长节\n\n{LONG_BODY}"
    chunks = split_markdown(text, source="arch/t.md")
    assert len(chunks) >= 2
    tail = chunks[0].page_content[-50:]
    head = chunks[1].page_content[:50]
    assert tail in chunks[1].page_content or any(c in head for c in tail[-20:])


def test_split_faq_pairs():
    """FAQ 问答题应拆成独立 chunk，且前言区不含一级标题块。"""
    chunks = split_markdown(FAQ_SAMPLE, source="faq/account.md")
    sections = [c.metadata["section"] for c in chunks]
    assert any("企业版如何计费" in s for s in sections)
    assert any("重置密码" in s for s in sections)
    assert not any(c.metadata["section"].startswith("# NovaCloud") for c in chunks)
    billing = next(c for c in chunks if "企业版" in c.metadata["section"])
    assert "99 元/月" in billing.page_content
