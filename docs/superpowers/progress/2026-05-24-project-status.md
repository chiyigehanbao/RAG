# RAG 架构助手 — 项目进度记录

> 最后更新：2026-05-24  
> 状态：**Phase 4 RAG 增强包已落地（overlap / corpus / BM25+RRF / eval / Trace 改写对比）**

---

## 1. 项目目标（一句话）

**RAG 架构助手**：自指知识库 `data/arch/` + **LangGraph** 可见执行（SSE）+ **LangChain/Chroma/DeepSeek/Ollama** 全栈作品集项目。

---

## 2. 已确认的设计决策

| 决策 | 选择 | 备注 |
|------|------|------|
| 演示场景 | 虚构 SaaS 企业文档（手册/Wiki/FAQ） | 8 个 Markdown |
| LLM | DeepSeek API | `.env` 中 `DEEPSEEK_API_KEY` |
| **Embedding** | **Ollama `nomic-embed-text`** | 不用 sentence-transformers / BGE |
| 向量库 | Chroma（`data/chroma/`） | ingest 前清库防重复 |
| 关系库 | SQLite | 会话、消息、trace |
| Agent | LangGraph Phase 1 | classify → retrieve → generate/refuse/chitchat |
| 前端 | React + Vite + Tailwind | 对话 + 调试面板 + 文档管理 |
| 中文 FAQ 检索 | 向量 + 关键词混合 | 弥补 nomic 中文语义弱 |

---

## 3. Task 完成度

| Task | 内容 | 状态 |
|------|------|------|
| 1–14 | 后端 RAG、Agent、API、虚拟数据 | ✅ |
| 15–19 | React 前端三页 + API client | ✅ |
| 20 | 根目录 `README.md` + Demo 验收 | ✅ |
| 21+ | Phase 2 grade/rewrite、BM25 等 | ⏸ 未做 |

---

## 4. Demo 验收（2026-05-24 通过）

| 问题 | 结果 |
|------|------|
| 企业版如何计费？ | ✅ 引用 FAQ，调试面板有 retrieve |
| 如何重置密码？ | ✅ 引用 faq/account.md |
| 你好 | ✅ chitchat，无 citations |
| 火星怎么登录？ | ✅ 拒答 |
| 调试面板 | ✅ 节点耗时 + chunks + distance |
| 文档管理 / 重新索引 | ✅ |

---

## 5. 启动命令速查

```powershell
# 终端 1 — 项目根目录 D:\RAG
venv\Scripts\activate
python -m backend.rag.ingest --source ./data
uvicorn backend.main:app --reload --port 8000

# 终端 2
cd frontend
npm run dev
```

前置：Ollama 运行 + `ollama pull nomic-embed-text`；`.env` 含 DeepSeek Key。

---

## 6. 调试会话中修复的问题

| 问题 | 根因 | 处理 |
|------|------|------|
| 一律拒答 | relevance score 为负 | 改用 L2 distance + `MAX_RETRIEVAL_DISTANCE` |
| 终端无检索日志 | uvicorn 只打 HTTP 日志 | 正常；详情在前端调试面板 / trace API |
| 调试面板不可见 | `hidden lg:block` | 窄屏改对话下方展示 |
| FAQ 检索不准 | nomic 中文弱 + chunker 问题 | FAQ 分块 + 关键词混合检索 |
| 重复 ingest | 未清 Chroma collection | ingest 前 `delete_collection` |

---

## 7. UI 改版（2026-05-24）

- 设计 spec：`docs/superpowers/specs/2026-05-24-novacloud-ui-redesign-design.md`
- 产品官网助手风格：Outfit/DM Sans、深海蓝+天青、Hero 示例卡、Agent 洞察侧栏

## 8. Phase 2

- 设计 spec：`docs/superpowers/specs/2026-05-24-phase2-agent-upload-design.md`
- **2a grade+rewrite**：✅ 已完成（图、助手设定、Trace 抽屉）
- **2b 文档上传**：✅ 已完成（`POST /api/documents/upload`、文档页拖拽上传）

## 9. Phase 4 RAG 增强包（2026-05-24）

- 规格：`docs/superpowers/specs/2026-05-24-rag-enhancement-pack-design.md`
- 计划：`docs/superpowers/plans/2026-05-24-rag-enhancement-pack.md`
- **4a** 长节 overlap 切片（800/100/400）+ `test_chunker`
- **4b** `corpus.py`、classify `corpus`、`retrieval_scope` 设定页、retriever `where`
- **4c** `bm25_store` + `rrf`、ingest 重建 BM25、`rank-bm25`
- **4d** `data/eval/golden_retrieval.jsonl` + `scripts/eval_retrieval`（本地 16/16 Hit@10）
- **4e** TraceDrawer 改写对比卡片、LiveRunTimeline / SSE 文案一致

## 10. 后续

- critique 节点 / 双路并行检索（见增强包 spec §10）
- 升级 `langchain-ollama` / `langchain-chroma` 消除 DeprecationWarning

---

## 11. 与原始 Spec 的差异

| Spec 原文 | 当前实际 |
|-----------|----------|
| Embedding: BGE | Ollama `nomic-embed-text` |
| `RETRIEVE_TOP_K=4` | 默认 10 |
| Phase 1 纯向量检索 | 增加 FAQ 关键词补充 |

实现以本仓库代码与 `README.md` 为准。
