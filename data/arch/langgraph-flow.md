# LangGraph Agent 流程

## 状态图

入口节点：**classify**（判断是否需要查知识库）

- 若 `route = no_rag` → **chitchat**（简短闲聊，不检索）
- 若 `route = need_rag` → **retrieve**（向量检索）

检索之后进入 **grade**（判断检索片段是否足以回答）：

- 相关 → **generate**（基于片段生成答案与引用）
- 不相关且未超重试次数 → **rewrite**（DeepSeek 改写检索 query）→ 再次 **retrieve**
- 不相关且已达重试上限 → **refuse**（返回拒答话术）

## 状态字段（AgentState）

| 字段 | 含义 |
|------|------|
| question | 用户当前问题 |
| chat_history | 多轮历史 |
| rewritten_question | 改写后的检索 query |
| retry_count | 已改写次数 |
| documents | 检索到的 chunks |
| is_relevant | grade 结果 |
| grade_reason | 评分原因（距离/空结果/LLM 等） |
| answer | 最终回答 |
| citations | 引用列表 |
| node_trace | 各节点耗时与输入输出摘要 |

## 与普通 Chain 的区别

普通 RAG 常为「检索 → 生成」单次链路。本项目的 **LangGraph** 显式建模：

- **条件路由**（是否检索、是否拒答）
- **循环**（rewrite → retrieve）
- **可观测**（每节点写入 node_trace，前端流式展示）

问：LangGraph 有哪些节点？  
答：classify、retrieve、grade、rewrite、generate、refuse、chitchat。
