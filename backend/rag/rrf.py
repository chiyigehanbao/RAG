"""Reciprocal Rank Fusion：合并多路检索候选。"""


def rrf_merge(ranked_lists: list[list[str]], k: int = 60, limit: int = 10) -> list[str]:
    """
    将多路有序 doc_key 列表用 RRF 合并。

    Args:
        ranked_lists: 每路按相关度降序的 key 列表
        k: RRF 常数，默认 60
        limit: 返回条数上限

    Returns:
        合并去重后的 key 列表
    """
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, key in enumerate(ranked, start=1):
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
    ordered = sorted(scores.keys(), key=lambda key: scores[key], reverse=True)
    return ordered[:limit]
