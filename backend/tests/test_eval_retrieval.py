"""eval_retrieval Hit 逻辑测试。"""
from scripts.eval_retrieval import hit_at_k


def test_hit_at_k_any_prefix():
    results = [
        {"source": "arch/langgraph-flow.md", "section": "节点"},
        {"source": "faq/other.md", "section": "x"},
    ]
    assert hit_at_k(results, ["arch/langgraph"], k=2)
    assert not hit_at_k(results, ["wiki/billing"], k=1)


def test_hit_at_k_empty_results():
    assert not hit_at_k([], ["arch/overview"], k=5)
