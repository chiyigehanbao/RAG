# RAG 增强包 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不做企业级能力的前提下，交付重叠切片、corpus 元数据过滤、BM25+向量 RRF 混合检索、检索层黄金集评测、Trace 改写对比 UI。

**Architecture:** 检索能力拆为独立模块（`corpus` / `bm25_store` / `rrf`），`retriever.py` 只负责编排；classify 输出 `corpus`，runtime `retrieval_scope` 可覆盖；ingest 同步重建 Chroma 与 BM25 索引。Agent 图结构不变（无 critique）。

**Tech Stack:** Python 3.11, FastAPI, LangGraph, Chroma, rank-bm25, Ollama embedding, React 19, pytest.

**Spec:** `docs/superpowers/specs/2026-05-24-rag-enhancement-pack-design.md`

**架构约束（code-architect）：** 新逻辑进 `backend/rag/` 小文件，单函数认知复杂度 <15；卫语句提前返回；新文件顶部 Docstring；ORM 仍只在 `backend/db/models.py`。

---

## 文件职责地图

| 文件 | 职责 |
|------|------|
| `backend/rag/chunker.py` | 分块 + overlap |
| `backend/rag/corpus.py` | `Corpus` 枚举、Chroma `where`、中文展示标签 |
| `backend/rag/bm25_store.py` | 构建/加载/查询 BM25 索引 |
| `backend/rag/rrf.py` | RRF 合并多路候选 |
| `backend/rag/retriever.py` | 向量 + BM25 + keyword → RRF |
| `backend/rag/ingest.py` | ingest 末尾调用 `bm25_store.rebuild` |
| `backend/agent/state.py` | 增加 `corpus`, `retrieval_corpus` |
| `backend/agent/prompts.py` | classify 输出 `corpus` |
| `backend/agent/nodes.py` | classify/retrieve 接入 corpus |
| `backend/runtime.py` | `retrieval_scope` |
| `scripts/eval_retrieval.py` | Hit@k 评测 |
| `data/eval/golden_retrieval.jsonl` | 黄金集 |

---

## Batch 4a — 重叠切片

### Task 1: 分块 overlap 测试

**Files:**
- Modify: `backend/tests/test_chunker.py`
- Modify: `backend/rag/chunker.py`

- [ ] **Step 1: 在 `chunker.py` 顶部增加常量**

```python
_MAX_SECTION_CHARS = 800
_OVERLAP_CHARS = 100
_MIN_SPLIT_CHARS = 400
```

- [ ] **Step 2: 写失败测试**

```python
LONG_BODY = "段落内容。" * 120  # > 400 字

def test_long_section_splits_with_overlap():
    text = f"# T\n\n## 长节\n\n{LONG_BODY}"
    chunks = split_markdown(text, source="arch/t.md")
    assert len(chunks) >= 2
    tail = chunks[0].page_content[-50:]
    head = chunks[1].page_content[:50]
    assert tail in chunks[1].page_content or any(c in head for c in tail[-20:])
```

- [ ] **Step 3: 运行测试确认 FAIL**

```bash
cd d:\RAG
venv\Scripts\python.exe -m pytest backend/tests/test_chunker.py::test_long_section_splits_with_overlap -v
```

- [ ] **Step 4: 实现 `_split_body_with_overlap(body, source, section)`**

逻辑：若 `len(body) <= _MIN_SPLIT_CHARS`，返回单块；否则按 `_MAX_SECTION_CHARS` 步进 `(_MAX_SECTION_CHARS - _OVERLAP_CHARS)` 切片。

- [ ] **Step 5: 在 `split_markdown` 非 FAQ 分支调用**

- [ ] **Step 6: 全量 chunker 测试通过**

```bash
venv\Scripts\python.exe -m pytest backend/tests/test_chunker.py -v
```

- [ ] **Step 7: Commit**（用户要求时）

```bash
git commit -m "feat(rag): add overlapping chunks for long sections"
```

---

## Batch 4b — 元数据过滤

### Task 2: corpus 模块

**Files:**
- Create: `backend/rag/corpus.py`
- Create: `backend/tests/test_corpus.py`

- [ ] **Step 1: 写 `corpus.py`**

```python
"""检索语料范围：与 classify / runtime 设定对齐的 Chroma 过滤。"""
from enum import Enum

class Corpus(str, Enum):
    ALL = "all"
    ARCH = "arch"
    BUSINESS = "business"

BUSINESS_PREFIXES = ("faq/", "wiki/", "product_manual/", "uploads/")

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
        return {"source": {"$regex": "^arch/"}}
    if corpus == Corpus.BUSINESS:
        return {
            "$or": [{"source": {"$regex": f"^{p}"}} for p in BUSINESS_PREFIXES]
        }
    return None

def corpus_label(corpus: Corpus) -> str:
    labels = {Corpus.ALL: "全部文档", Corpus.ARCH: "架构文档", Corpus.BUSINESS: "业务文档"}
    return labels[corpus]
```

> 若 Chroma 版本不支持 `$regex`，改用 ingest 时写入 `metadata["corpus"]` 字段并在 where 用 `$eq`（实现时以本地 Chroma 行为为准，测试锁定）。

- [ ] **Step 2: 测试 `resolve_corpus` 与 `chroma_where`**

- [ ] **Step 3: Commit**

### Task 3: classify 输出 corpus

**Files:**
- Modify: `backend/agent/state.py`
- Modify: `backend/agent/prompts.py`
- Modify: `backend/agent/nodes.py`
- Modify: `backend/tests/test_graph.py`（mock LLM JSON）

- [ ] **Step 1: `AgentState` 增加字段**

```python
corpus: str  # arch | business | all
retrieval_corpus: str  # 解析后的最终 corpus
```

- [ ] **Step 2: 更新 `CLASSIFY_PROMPT`**

`need_rag` 时输出：`{"route":"need_rag","corpus":"arch"}`，并说明 arch/business/all 含义。

- [ ] **Step 3: `classify_node` 解析 `corpus`，trace output 含 `corpus`**

- [ ] **Step 4: `retrieve_node` 调用 `resolve_corpus` + 写入 `retrieval_corpus`**

```python
from backend.rag.corpus import resolve_corpus, chroma_where, corpus_label
runtime = load_runtime()
final = resolve_corpus(state.get("corpus"), runtime.retrieval_scope)
where = chroma_where(final)
docs = retrieve_with_scores(query, top_k=None, where=where)
# trace output: retrieval_scope_label=corpus_label(final)
```

- [ ] **Step 5: 更新 mock 测试 LLM 返回含 corpus 的 JSON**

- [ ] **Step 6: `pytest backend/tests/test_graph.py -v`**

### Task 4: runtime + API + 前端设定

**Files:**
- Modify: `backend/runtime.py`
- Modify: `backend/schemas/settings.py`
- Modify: `backend/api/settings.py`
- Modify: `backend/tests/test_settings_api.py`
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/pages/SettingsPage.tsx`
- Modify: `frontend/src/lib/labels.ts`（可选展示文案）

- [ ] **Step 1: `RuntimeSettings` 增加**

```python
retrieval_scope: str = Field(default="auto")  # auto|all|arch_only|business_only
```

- [ ] **Step 2: Pydantic `SettingsOut` / `SettingsUpdate` 同步**

- [ ] **Step 3: 设定页增加「检索范围」下拉框**

- [ ] **Step 4: 测试 settings API 默认值**

- [ ] **Step 5: Commit**

### Task 5: retriever 支持 where

**Files:**
- Modify: `backend/rag/retriever.py`
- Modify: `backend/tests/test_retriever.py`

- [ ] **Step 1: `retrieve_with_scores(query, top_k=None, where=None)`**

向量检索传入 `filter=where`；keyword 搜索仅在 where 允许的行 id 上匹配（先 `collection.get(where=where)` 或检索后过滤）。

- [ ] **Step 2: 测试带 arch filter 不返回 faq 路径**

---

## Batch 4c — BM25 + RRF

### Task 6: BM25 存储

**Files:**
- Create: `backend/rag/bm25_store.py`
- Modify: `backend/requirements.txt`
- Modify: `backend/rag/ingest.py`

- [ ] **Step 1: 添加依赖**

```
rank-bm25>=0.2.2
```

- [ ] **Step 2: `bm25_store.py` 实现**

```python
"""BM25 索引：与 Chroma 共用 chunk 列表，ingest 时重建。"""
INDEX_PATH = Path("./data/bm25/index.pkl")

def rebuild(chunks: list[Document]) -> None: ...
def load() -> Bm25Index | None: ...
def search(query: str, top_n: int, allowed_indices: set[int] | None) -> list[tuple[int, float]]: ...
```

- 分词：简单按 `\w+` + 中文单字切分即可（YAGNI，不引入 jieba）。

- [ ] **Step 3: `ingest.py` 全量/单文件入库后调用 `rebuild(all_chunks)`**

全量 ingest 收集所有 chunks 一次 rebuild；单文件 upload 后从 Chroma get 全量或增量更新索引（优先：**每次 ingest 结束 reload 全库 metadata 重建 BM25**，简单可靠）。

- [ ] **Step 4: 测试 rebuild + search 命中已知词**

### Task 7: RRF 合并

**Files:**
- Create: `backend/rag/rrf.py`
- Create: `backend/tests/test_rrf.py`

- [ ] **Step 1: 实现 `rrf_merge(ranked_lists: list[list[str]], k: int = 60, limit: int) -> list[str]`**

输入为 doc_key 有序列表；输出合并后的 key 列表。

- [ ] **Step 2: 测试两路列表合并顺序稳定**

### Task 8: 接入 retriever

**Files:**
- Modify: `backend/rag/retriever.py`

- [ ] **Step 1: 三路候选**

1. `vector_pairs` with filter  
2. `bm25_store.search` → 映射回 doc  
3. `_keyword_search`（保留）

- [ ] **Step 2: RRF → `_merge_results` 输出带 `channel`**

- [ ] **Step 3: 更新 `test_retriever.py` mocks**

- [ ] **Step 4: 全量 pytest**

```bash
venv\Scripts\python.exe -m pytest backend/tests -q
```

### Task 9: README 检索对比表

**Files:**
- Modify: `README.md`
- Optional: `data/arch/rag-pipeline.md`

- [ ] **Step 1: 增加 Phase 3 vs Phase 4 表格与 reindex / BM25 说明**

---

## Batch 4d — 检索评测

### Task 10: 黄金集 + 脚本

**Files:**
- Create: `data/eval/golden_retrieval.jsonl`
- Create: `scripts/eval_retrieval.py`
- Create: `backend/tests/test_eval_retrieval.py`

- [ ] **Step 1: 编写 12–16 条 JSONL**

示例：

```json
{"question": "LangGraph 有哪些节点", "expected_sources": ["arch/langgraph"], "corpus": "arch"}
{"question": "企业版如何计费", "expected_sources": ["faq/account", "wiki/billing"], "corpus": "business"}
```

- [ ] **Step 2: `scripts/eval_retrieval.py`**

```python
"""检索层 Hit@k 评测（不调用 LLM）。"""
def hit_at_k(question, expected_prefixes, corpus, k) -> bool: ...
def main():
    # load golden, loop retrieve_with_scores, print table, sys.exit(1 if rate < 0.8)
```

- [ ] **Step 3: 单元测试 hit 逻辑（mock 返回）**

- [ ] **Step 4: 本地跑通（需 Ollama + ingest）**

```bash
python -m backend.rag.ingest --source ./data
python -m scripts.eval_retrieval
```

---

## Batch 4e — Trace 改写对比 UI

### Task 11: TraceDrawer 对比卡片

**Files:**
- Modify: `frontend/src/components/TraceDrawer.tsx`
- Modify: `frontend/src/components/LiveRunTimeline.tsx`

- [ ] **Step 1: 抽取 `RewriteCompareCard`（同文件内小组件）**

两列布局：原 query | 改写后 query；显示 `retry_count`。

- [ ] **Step 2: 替换现有 rewrite 小节为对比卡片**

- [ ] **Step 3: `LiveRunTimeline` rewrite detail 与卡片文案一致**

- [ ] **Step 4: 手动验证：问「企业版贵不贵」或口语计费触发 rewrite**

---

## 最终验收

- [ ] `pytest backend/tests -q` 全绿  
- [ ] `python -m backend.rag.ingest --source ./data` 成功  
- [ ] `python -m scripts.eval_retrieval` 命中率 ≥ 80%  
- [ ] 对话页：架构题仅 arch 引用（auto）  
- [ ] 设定页切换检索范围生效  
- [ ] Trace 抽屉改写对比可见  

---

## Spec 覆盖自检

| Spec 章节 | 任务 |
|-----------|------|
| §3 overlap | Task 1 |
| §4 corpus filter | Task 2–5 |
| §5 BM25+RRF | Task 6–9 |
| §6 eval | Task 10 |
| §7 Trace UI | Task 11 |
| §10 后续迭代 | 无任务（仅 spec 记录） |

---

## 执行后文档

- 更新 `docs/superpowers/progress/2026-05-24-project-status.md` 增加 Phase 4 完成项
