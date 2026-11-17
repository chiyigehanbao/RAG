# 常见问题

问：rewrite 什么时候触发？  
答：当 grade 判定检索片段不足以回答当前问题，且改写重试次数未达上限时，会进入 rewrite 节点改写 query，再回到 retrieve。

问：DeepSeek API Key 用在哪里？  
答：用于 LangGraph 中的 classify、generate、rewrite、chitchat，以及可选的 grade LLM 判断；Embedding 走 Ollama，不用该 Key。

问：Embedding 用的什么？  
答：默认 Ollama 本地模型 `nomic-embed-text`，在 ingest 与向量检索时调用。

问：如何看到 LangGraph 执行过程？  
答：使用流式接口 `/api/chat/stream`，前端会实时显示各节点（理解问题、查找资料、判断、改写、组织回答）的执行链路。

问：知识库文档存在哪？  
答：Markdown 在 `data/` 目录，向量在 `data/chroma/`，会话在 SQLite。
