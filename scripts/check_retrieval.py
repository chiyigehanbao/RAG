"""临时脚本：检查检索 top-k 结果。"""
from backend.config import get_settings
from backend.rag.retriever import _get_vectorstore, retrieve_with_scores

get_settings.cache_clear()
_get_vectorstore.cache_clear()

queries = ["企业版如何计费？", "如何重置密码？"]
for q in queries:
    print("===", q)
    for r in retrieve_with_scores(q)[:3]:
        print(
            round(r["distance"], 1),
            r["source"],
            r["section"][:40],
            r["content"][:80].replace("\n", " "),
        )
