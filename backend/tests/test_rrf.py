"""RRF 合并测试。"""
from backend.rag.rrf import rrf_merge


def test_rrf_merge_two_lists_stable():
    list_a = ["doc1", "doc2", "doc3"]
    list_b = ["doc2", "doc4", "doc1"]
    merged = rrf_merge([list_a, list_b], k=60, limit=4)
    assert merged[0] in ("doc1", "doc2")
    assert "doc4" in merged
    assert len(merged) == 4
    assert len(set(merged)) == len(merged)
