"""corpus 模块测试。"""
from backend.rag.corpus import (
    Corpus,
    chroma_where,
    corpus_for_source,
    corpus_label,
    resolve_corpus,
)


def test_corpus_for_source():
    assert corpus_for_source("arch/overview.md") == "arch"
    assert corpus_for_source("faq/account.md") == "business"
    assert corpus_for_source("wiki/deploy.md") == "business"
    assert corpus_for_source("other/readme.md") == "other"


def test_resolve_corpus_auto_uses_classify():
    assert resolve_corpus("arch", "auto") == Corpus.ARCH
    assert resolve_corpus("business", "auto") == Corpus.BUSINESS
    assert resolve_corpus(None, "auto") == Corpus.ALL


def test_resolve_corpus_scope_overrides():
    assert resolve_corpus("arch", "all") == Corpus.ALL
    assert resolve_corpus("business", "arch_only") == Corpus.ARCH
    assert resolve_corpus("arch", "business_only") == Corpus.BUSINESS


def test_chroma_where():
    assert chroma_where(Corpus.ALL) is None
    assert chroma_where(Corpus.ARCH) == {"corpus": {"$eq": "arch"}}
    assert chroma_where(Corpus.BUSINESS) == {"corpus": {"$eq": "business"}}


def test_corpus_label():
    assert corpus_label(Corpus.ARCH) == "架构文档"
