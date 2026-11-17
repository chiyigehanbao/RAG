# RAG 架构助手 — 系统概览

## 产品定位

**RAG 架构助手** 是一款面向技术学习的本地知识库问答系统，核心用于实践并展示：

- **LangGraph**：有状态 Agent 编排（条件边、改写循环）
- **LangChain**：文档抽象、向量库、LLM 调用
- **RAG**：分块、向量索引、检索增强生成
- **Embedding**：Ollama 本地向量化

## 请求全链路

1. 用户在前端提问，请求到达 FastAPI `/api/chat` 或 `/api/chat/stream`。
2. 从 SQLite 加载同会话历史，构造多轮上下文。
3. **LangGraph** 按节点执行：分类 → 检索 → 评分 →（可选）改写 → 生成或拒答。
4. **检索** 使用 Chroma 向量库 + FAQ 关键词补充；Embedding 由 Ollama 完成。
5. **生成** 使用 DeepSeek API（OpenAI 兼容接口），基于检索片段组织答案并附引用。
6. 消息与节点 trace 写入 SQLite，前端可展示执行链路与引用来源。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React、Vite、TypeScript |
| 后端 | FastAPI |
| Agent | LangGraph |
| RAG | LangChain、ChromaDB |
| 推理 LLM | DeepSeek |
| 向量 | Ollama `nomic-embed-text` |
| 业务库 | SQLite |
