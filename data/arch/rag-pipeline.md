# RAG 管道：分块、索引与检索

## 1. 文档来源

- 内置技术文档目录 `data/arch/`（本系统说明）
- 用户上传的 Markdown：`data/uploads/`
- 可通过文档管理页 **重建全库索引** 或 **单文件增量索引**

## 2. 分块（Chunking）

策略见 `backend/rag/chunker.py`：

- 按 Markdown **二级标题** `##` 切分
- **FAQ** 按「问：/答：」拆成独立块，便于精确命中
- 每块元数据：`source`（文件路径）、`section`（章节名）

问：什么是切片？  
答：即将长文档拆成较小文本块再向量化，检索时按块命中而非整篇文档。

## 3. 索引（Ingest）

- **Embedding**：Ollama 本地模型（默认 `nomic-embed-text`），不消耗 DeepSeek 额度
- **向量库**：Chroma，持久化目录 `data/chroma/`
- **全量索引**：清空 collection 后扫描 `data/` 下所有 `.md`
- **增量索引**：上传或单文件更新时，仅替换该 `source` 对应向量

## 4. 检索（Retrieve）

- 向量 top-k（条数可在系统设定中调整）
- 对 FAQ 类文档辅以 **关键词匹配**，缓解中文语义向量偏弱的问题
- 使用 **L2 距离** 衡量相似度，距离越小越相关；grade 节点结合阈值与可选 LLM 判断

## 5. 生成（Generate）

将命中 chunks 拼入 Prompt，由 **DeepSeek** 生成答案，并列出引用来源。
