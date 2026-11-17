"""BM25 索引：与 Chroma 共用 chunk 列表，ingest 时重建。"""
import pickle
import re
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

INDEX_PATH = Path("./data/bm25/index.pkl")


def _tokenize(text: str) -> list[str]:
    """简单分词：英文词 + 中文单字。"""
    tokens = re.findall(r"\w+", text.lower())
    tokens.extend(c for c in text if "\u4e00" <= c <= "\u9fff")
    return tokens


@dataclass
class Bm25Index:
    """持久化的 BM25 索引与 chunk 元数据。"""

    bm25: BM25Okapi
    chunks: list[dict]


def rebuild(chunks: list[Document]) -> None:
    """从 Document 列表重建 BM25 索引并写入磁盘。"""
    records = [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("source", ""),
            "section": doc.metadata.get("section", ""),
            "corpus": doc.metadata.get("corpus", "other"),
        }
        for doc in chunks
    ]
    if not records:
        if INDEX_PATH.exists():
            INDEX_PATH.unlink()
        return

    tokenized = [_tokenize(r["content"] + " " + r["section"]) for r in records]
    bm25 = BM25Okapi(tokenized)
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("wb") as f:
        pickle.dump(Bm25Index(bm25=bm25, chunks=records), f)


def load() -> Bm25Index | None:
    """加载索引；不存在则返回 None。"""
    if not INDEX_PATH.exists():
        return None
    with INDEX_PATH.open("rb") as f:
        return pickle.load(f)


def search(
    query: str,
    top_n: int,
    allowed_indices: set[int] | None = None,
) -> list[tuple[int, float]]:
    """
    BM25 检索。

    Args:
        query: 用户问题
        top_n: 最多返回条数
        allowed_indices: 允许的 chunk 下标子集（corpus 过滤）

    Returns:
        (chunk_index, score) 列表，按分数降序
    """
    index = load()
    if index is None or not index.chunks:
        return []

    scores = index.bm25.get_scores(_tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    results: list[tuple[int, float]] = []
    for i in ranked:
        if allowed_indices is not None and i not in allowed_indices:
            continue
        results.append((i, float(scores[i])))
        if len(results) >= top_n:
            break
    return results
