# Phase 3：技术透视版 — 设计规格

> 状态：已批准（2026-05-24）  
> 产品名：**RAG 架构助手**  
> 目标：本地运行，凸显 LangGraph + LangChain + RAG + Embedding，不堆 SaaS 功能

---

## 1. 原则

- 不做行业虚构案例、不做评测脚本、不做 BM25 混合（除非后续单独迭代）
- 核心：**LangGraph 执行链路默认可见（SSE）** + 自指 `data/arch/` 知识库
- 文案去除 demo / 演示 / 虚构 SaaS 叙事

---

## 2. 知识库

`data/arch/`：README 提炼、LangGraph 流程、RAG 管道、LangChain 用法、配置说明、FAQ。

---

## 3. 流式 API

`POST /api/chat/stream`：SSE 推送 `node` / `token` / `done` / `error` 事件；结束后持久化 SQLite trace。

---

## 4. 前端

- 问答页：执行链路时间轴 + 流式答案（默认展开）
- 文档页：分块预览 `GET /api/documents/chunks?path=`
- 系统设定：模型与依赖说明（只读）

---

## 5. 批次

| 批次 | 内容 |
|------|------|
| 3.1 | arch 文档、品牌、README、去 demo 文案 |
| 3.2 | SSE + 流式 UI |
| 3.3 | 分块预览 API/UI |

---

## 6. 验收

- [ ] 问「LangGraph 有哪些节点」可引用 arch 文档
- [ ] 提问时执行链路实时显示
- [ ] 答案流式输出
- [ ] 文档页可看 chunk 列表
- [ ] 无 demo/演示字样
