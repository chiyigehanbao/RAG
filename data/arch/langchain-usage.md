# 本项目中 LangChain 的用法

LangChain 在本仓库中承担 **RAG 基础设施**，不负责 Agent 分支逻辑（分支由 LangGraph 负责）。

## 使用的组件

| 模块 | LangChain 能力 | 路径 |
|------|----------------|------|
| 文档 | `langchain_core.documents.Document` | `chunker.py` |
| Embedding | `OllamaEmbeddings` | `embeddings.py` |
| 向量库 | `Chroma` 向量存储 | `ingest.py`、`retriever.py` |
| 对话模型 | `ChatOpenAI` 对接 DeepSeek | `llm.py`、`nodes.py` |

## 与 LangGraph 的分工

- **LangGraph**：`StateGraph` 定义节点与边，`graph.invoke` / `graph.stream` 执行编排。
- **LangChain**：提供 Document、Embedding、VectorStore、ChatModel 等积木。

问：LangChain 和 LangGraph 分别做什么？  
答：LangChain 提供 RAG 与 LLM 调用封装；LangGraph 负责多步骤 Agent 状态机与条件/循环。
