"""BM25 索引测试。"""
from pathlib import Path

import pytest
from langchain_core.documents import Document

from backend.rag import bm25_store


@pytest.fixture
def temp_index(tmp_path, monkeypatch):
    monkeypatch.setattr(bm25_store, "INDEX_PATH", tmp_path / "index.pkl")
    yield tmp_path / "index.pkl"


def test_rebuild_and_search_hits(temp_index):
    chunks = [
        Document(
            page_content="LangGraph 节点包括 classify 与 retrieve",
            metadata={"source": "arch/langgraph.md", "section": "节点", "corpus": "arch"},
        ),
        Document(
            page_content="企业版按年订阅计费",
            metadata={"source": "faq/billing.md", "section": "计费", "corpus": "business"},
        ),
    ]
    bm25_store.rebuild(chunks)
    hits = bm25_store.search("classify retrieve", top_n=2, allowed_indices=None)
    assert hits
    idx, score = hits[0]
    assert score >= 0
    loaded = bm25_store.load()
    assert loaded is not None
    assert "LangGraph" in loaded.chunks[idx]["content"]
