"""Retriever 测试。"""
from unittest.mock import patch

from langchain_core.documents import Document

from backend.rag.retriever import _merge_results_rrf, retrieve_with_scores


@patch("backend.rag.retriever._bm25_pairs")
@patch("backend.rag.retriever._keyword_search")
@patch("backend.rag.retriever._get_vectorstore")
def test_retrieve_with_scores_returns_scored_docs(mock_vs, mock_kw, mock_bm25):
    """应返回带 score 与 distance 的文档列表。"""
    mock_kw.return_value = []
    mock_bm25.return_value = []
    doc = Document(page_content="test", metadata={"source": "a.md", "section": "S"})
    mock_vs.return_value.similarity_search_with_score.return_value = [(doc, 100.0)]

    results = retrieve_with_scores("query", where=None)
    assert len(results) == 1
    assert results[0]["distance"] == 100.0
    assert results[0]["score"] == round(1.0 / 101.0, 4)
    assert results[0]["source"] == "a.md"


def test_merge_results_rrf_includes_channels():
    """RRF 合并应保留 channel 字段。"""
    kw_doc = Document(page_content="企业版计费", metadata={"source": "faq/a.md", "section": "概要"})
    vec_doc = Document(page_content="无关", metadata={"source": "b.md", "section": "X"})

    merged = _merge_results_rrf([(kw_doc, 80.0)], [(vec_doc, 300.0)], [], limit=2)
    channels = {m["channel"] for m in merged}
    assert "keyword" in channels
    assert "vector" in channels


@patch("backend.rag.retriever._bm25_pairs")
@patch("backend.rag.retriever._keyword_search")
@patch("backend.rag.retriever._get_vectorstore")
def test_retrieve_arch_filter_excludes_faq(mock_vs, mock_kw, mock_bm25):
    """arch 过滤时不应返回 faq 路径文档。"""
    mock_kw.return_value = []
    mock_bm25.return_value = []
    faq = Document(page_content="计费", metadata={"source": "faq/billing.md", "section": "S"})
    arch = Document(page_content="LangGraph", metadata={"source": "arch/langgraph.md", "section": "S"})
    mock_vs.return_value.similarity_search_with_score.return_value = [(arch, 50.0)]

    where = {"corpus": {"$eq": "arch"}}
    results = retrieve_with_scores("LangGraph 节点", where=where)
    mock_vs.return_value.similarity_search_with_score.assert_called_once()
    call_kwargs = mock_vs.return_value.similarity_search_with_score.call_args
    assert call_kwargs.kwargs.get("filter") == where
    assert all("faq/" not in r["source"] for r in results)
    assert results[0]["source"] == "arch/langgraph.md"
