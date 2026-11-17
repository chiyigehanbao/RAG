# 配置说明

配置文件：项目根目录 `.env`（参考 `.env.example`）。

## DeepSeek（推理）

| 变量 | 作用 |
|------|------|
| DEEPSEEK_API_KEY | API 密钥，用于分类、生成、改写、边界评分 |
| DEEPSEEK_BASE_URL | 默认 `https://api.deepseek.com/v1` |
| DEEPSEEK_MODEL | 默认 `deepseek-chat` |

**使用节点**：classify、generate、rewrite、chitchat；grade 在边界情况下可选调用。

密钥仅在后端读取，不会出现在前端或知识库文档中。

## Ollama（Embedding）

| 变量 | 作用 |
|------|------|
| OLLAMA_BASE_URL | 默认 `http://localhost:11434` |
| OLLAMA_EMBEDDING_MODEL | 默认 `nomic-embed-text` |

用于 ingest 与 retrieve 阶段的向量化，**不使用 DeepSeek Key**。

## 检索

| 变量 | 作用 |
|------|------|
| RETRIEVE_TOP_K | 检索返回条数 |
| MAX_RETRIEVAL_DISTANCE | L2 距离上限，越大越宽松 |

部分参数可在前端 **系统设定** 覆盖（写入 `data/runtime_settings.json`）。

## 存储

| 变量 | 作用 |
|------|------|
| CHROMA_PERSIST_DIR | Chroma 目录，默认 `./data/chroma` |
| SQLITE_URL | 会话与 trace，默认 `./db/novacloud.db` |
