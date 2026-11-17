"""Ingest 管道测试。"""
import pytest

from backend.rag.chunker import split_markdown


def test_split_faq_format():
    """FAQ 问答题应被正确分块。"""
    text = "问：如何重置密码？\n答：点击登录页忘记密码链接。"
    chunks = split_markdown(f"## 账号\n\n{text}", source="faq/account.md")
    assert any("重置密码" in c.page_content for c in chunks)


@pytest.mark.skip(reason="集成测试需 chromadb + Ollama，依赖装完后取消 skip")
def test_ingest_directory(tmp_path):
    """ingest 应处理目录下所有 md 文件。"""
    from backend.rag.ingest import ingest_directory

    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "billing.md").write_text("## 企业版定价\n\n每席位 99 元/月。", encoding="utf-8")

    count = ingest_directory(str(tmp_path), chroma_dir=str(tmp_path / "chroma"))
    assert count >= 1
