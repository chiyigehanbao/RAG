"""检索层 Hit@k 评测（不调用 LLM）。"""
import json
import sys
from pathlib import Path

from backend.rag.corpus import chroma_where, resolve_corpus
from backend.rag.retriever import retrieve_with_scores
from backend.runtime import load_runtime

GOLDEN_PATH = Path(__file__).resolve().parents[1] / "data" / "eval" / "golden_retrieval.jsonl"
PASS_RATE = 0.8


def hit_at_k(
    results: list[dict],
    expected_prefixes: list[str],
    k: int,
) -> bool:
    """任一 top-k 结果的 source 命中 expected 前缀即算对。"""
    sources = [str(r.get("source", "")) for r in results[:k]]
    return any(
        any(src.startswith(prefix) for prefix in expected_prefixes) for src in sources
    )


def main() -> None:
    runtime = load_runtime()
    k = runtime.retrieve_top_k
    if not GOLDEN_PATH.exists():
        print(f"Missing golden set: {GOLDEN_PATH}")
        sys.exit(1)

    cases: list[dict] = []
    for line in GOLDEN_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(json.loads(line))

    hits = 0
    print(f"Hit@{k} on {len(cases)} questions\n")
    print(f"{'OK':<4} {'question':<32} expected")
    print("-" * 72)

    for case in cases:
        question = case["question"]
        expected = case["expected_sources"]
        corpus = case.get("corpus", "all")
        final = resolve_corpus(corpus, "auto")
        where = chroma_where(final)
        results = retrieve_with_scores(question, top_k=k, where=where)
        ok = hit_at_k(results, expected, k)
        hits += int(ok)
        mark = "Y" if ok else "N"
        print(f"{mark:<4} {question[:30]:<32} {expected}")

    rate = hits / len(cases) if cases else 0.0
    print("-" * 72)
    print(f"Hit rate: {hits}/{len(cases)} = {rate:.1%}")
    if rate < PASS_RATE:
        sys.exit(1)


if __name__ == "__main__":
    main()
