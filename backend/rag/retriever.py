"""Chroma 向量检索 + 关键词补充，返回带分数的 chunks。"""
import re
from functools import lru_cache

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from backend.config import get_settings
from backend.runtime import load_runtime
from backend.rag.bm25_store import load as load_bm25_index
from backend.rag.bm25_store import search as bm25_search
from backend.rag.embeddings import get_embedding_function
from backend.rag.rrf import rrf_merge

# 关键词命中视为强相关（L2 距离远小于拒答阈值 450）
_KEYWORD_MATCH_DISTANCE = 80.0

_QUERY_STOP_WORDS = ("如何", "怎么", "怎样", "什么", "为什么", "吗", "呢", "是否")


def _distance_to_score(distance: float) -> float:
    """将 L2 距离映射为 (0,1] 展示分数，仅用于 UI。"""
    return round(1.0 / (1.0 + float(distance)), 4)


def _normalize_query_terms(query: str) -> list[str]:
    """提取可用于子串匹配的中文关键词（含原问句与去停用词变体）。"""
    text = re.sub(r"[？?。．.\s]+", "", query.strip())
    terms: list[str] = []

    if len(text) >= 2:
        terms.append(text)

    stripped = text
    for word in _QUERY_STOP_WORDS:
        stripped = stripped.replace(word, "")
    if len(stripped) >= 2 and stripped not in terms:
        terms.append(stripped)

    for sep in ("如何", "怎么", "怎样"):
        if sep not in text:
            continue
        prefix, _, suffix = text.partition(sep)
        if len(prefix) >= 2 and prefix not in terms:
            terms.append(prefix)
        if len(suffix) >= 2 and suffix not in terms:
            terms.append(suffix)

    return terms


def _doc_key(doc: Document) -> str:
    """用于去重与 RRF 的 chunk 标识。"""
    return (
        f"{doc.metadata.get('source', '')}|"
        f"{doc.metadata.get('section', '')}|"
        f"{doc.page_content[:80]}"
    )


def _allowed_bm25_indices(where: dict | None) -> set[int] | None:
    """根据 Chroma where 得到 BM25 允许的 chunk 下标。"""
    index = load_bm25_index()
    if index is None or where is None:
        return None
    corpus_clause = where.get("corpus")
    if not isinstance(corpus_clause, dict) or "$eq" not in corpus_clause:
        return None
    want = corpus_clause["$eq"]
    return {i for i, c in enumerate(index.chunks) if c.get("corpus") == want}


def _bm25_pairs(query: str, top_n: int, where: dict | None) -> list[tuple[Document, float]]:
    """BM25 检索并映射为 (Document, pseudo_distance)。"""
    if load_bm25_index() is None:
        return []
    allowed = _allowed_bm25_indices(where)
    hits = bm25_search(query, top_n, allowed)
    index = load_bm25_index()
    if index is None:
        return []
    pairs: list[tuple[Document, float]] = []
    for idx, score in hits:
        chunk = index.chunks[idx]
        doc = Document(
            page_content=chunk["content"],
            metadata={
                "source": chunk["source"],
                "section": chunk["section"],
                "corpus": chunk.get("corpus", "other"),
            },
        )
        pairs.append((doc, max(1.0, 200.0 - score)))
    return pairs


def _source_matches_where(source: str, where: dict | None) -> bool:
    """判断 source 是否满足 Chroma where（仅支持 corpus $eq）。"""
    if where is None:
        return True
    corpus_clause = where.get("corpus")
    if isinstance(corpus_clause, dict) and "$eq" in corpus_clause:
        from backend.rag.corpus import corpus_for_source

        return corpus_for_source(source) == corpus_clause["$eq"]
    return True


def _keyword_search(
    vectorstore: Chroma,
    query: str,
    limit: int = 5,
    where: dict | None = None,
) -> list[tuple[Document, float]]:
    """
    在已入库文档中做子串匹配，弥补 nomic 对中文语义检索偏弱的问题。

    Args:
        vectorstore: Chroma 实例
        query: 用户问题
        limit: 最多返回条数

    Returns:
        (Document, distance) 列表
    """
    terms = _normalize_query_terms(query)
    if not terms:
        return []

    collection = vectorstore._collection
    payload = collection.get(include=["documents", "metadatas"])
    hits: list[tuple[Document, float]] = []

    for content, meta in zip(payload["documents"], payload["metadatas"]):
        meta = meta or {}
        source = meta.get("source", "")
        if not _source_matches_where(source, where):
            continue
        section = meta.get("section", "")
        haystack = f"{section}\n{content}"
        if any(term in haystack for term in terms):
            hits.append((Document(page_content=content, metadata=meta), _KEYWORD_MATCH_DISTANCE))

    return hits[:limit]


def _register_candidate(
    lookup: dict[str, tuple[Document, float, str]],
    doc: Document,
    distance: float,
    channel: str,
) -> None:
    """登记候选；同 key 保留首次出现的 channel。"""
    key = _doc_key(doc)
    if key not in lookup:
        lookup[key] = (doc, float(distance), channel)


def _merge_results_rrf(
    keyword_pairs: list[tuple[Document, float]],
    vector_pairs: list[tuple[Document, float]],
    bm25_pairs: list[tuple[Document, float]],
    limit: int,
) -> list[dict]:
    """三路 RRF 合并，输出带 channel 的结果。"""
    lookup: dict[str, tuple[Document, float, str]] = {}
    ranked_lists: list[list[str]] = []

    for pairs, channel in (
        (vector_pairs, "vector"),
        (bm25_pairs, "bm25"),
        (keyword_pairs, "keyword"),
    ):
        keys: list[str] = []
        for doc, distance in pairs:
            _register_candidate(lookup, doc, distance, channel)
            keys.append(_doc_key(doc))
        if keys:
            ranked_lists.append(keys)

    if not ranked_lists:
        return []

    merged_keys = rrf_merge(ranked_lists, limit=limit)
    merged: list[dict] = []
    for key in merged_keys:
        doc, dist, channel = lookup[key]
        merged.append(
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "section": doc.metadata.get("section", ""),
                "distance": round(dist, 4),
                "score": _distance_to_score(dist),
                "channel": channel,
            }
        )
    return merged


@lru_cache
def _get_vectorstore() -> Chroma:
    """返回持久化 Chroma 实例。"""
    settings = get_settings()
    return Chroma(
        collection_name="novacloud",
        embedding_function=get_embedding_function(),
        persist_directory=settings.chroma_persist_dir,
    )


def retrieve_with_scores(
    query: str, top_k: int | None = None, where: dict | None = None
) -> list[dict]:
    """
    语义检索 top-k 文档块，并用关键词匹配补充 FAQ 类问题。

    Ollama + Chroma 返回的是 L2 距离（越小越相似），
    不能用 similarity_search_with_relevance_scores（会得到负数）。

    Args:
        query: 用户问题或改写 query
        top_k: 返回数量，默认读配置
        where: Chroma metadata 过滤子句

    Returns:
        含 content, source, section, score, distance 的字典列表
    """
    k = top_k or load_runtime().retrieve_top_k
    candidate_k = k * 2
    vectorstore = _get_vectorstore()

    keyword_pairs = _keyword_search(vectorstore, query, limit=candidate_k, where=where)
    vector_pairs = vectorstore.similarity_search_with_score(
        query, k=candidate_k, filter=where
    )
    bm25_pairs = _bm25_pairs(query, candidate_k, where)

    return _merge_results_rrf(keyword_pairs, vector_pairs, bm25_pairs, k)
