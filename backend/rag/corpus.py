"""检索语料范围：与 classify / runtime 设定对齐的 Chroma 过滤。"""
from enum import Enum

class Corpus(str, Enum):
    ALL = "all"
    ARCH = "arch"
    BUSINESS = "business"


BUSINESS_PREFIXES = ("faq/", "wiki/", "product_manual/", "uploads/")


def corpus_for_source(source: str) -> str:
    """根据 source 路径推断 corpus 元数据值。"""
    if source.startswith("arch/"):
        return Corpus.ARCH.value
    if any(source.startswith(p) for p in BUSINESS_PREFIXES):
        return Corpus.BUSINESS.value
    return "other"


def resolve_corpus(classify_corpus: str | None, retrieval_scope: str) -> Corpus:
    """根据设定页覆盖与 classify 结果得到最终 corpus。"""
    if retrieval_scope == "all":
        return Corpus.ALL
    if retrieval_scope == "arch_only":
        return Corpus.ARCH
    if retrieval_scope == "business_only":
        return Corpus.BUSINESS
    try:
        return Corpus(classify_corpus or "all")
    except ValueError:
        return Corpus.ALL


def chroma_where(corpus: Corpus) -> dict | None:
    """生成 Chroma where 子句；ALL 返回 None。"""
    if corpus == Corpus.ARCH:
        return {"corpus": {"$eq": Corpus.ARCH.value}}
    if corpus == Corpus.BUSINESS:
        return {"corpus": {"$eq": Corpus.BUSINESS.value}}
    return None


def corpus_label(corpus: Corpus) -> str:
    labels = {
        Corpus.ALL: "全部文档",
        Corpus.ARCH: "架构文档",
        Corpus.BUSINESS: "业务文档",
    }
    return labels[corpus]
