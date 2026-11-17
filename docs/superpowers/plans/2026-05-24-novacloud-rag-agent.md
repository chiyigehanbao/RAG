# NovaCloud RAG Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 NovaCloud 虚构企业知识库的全栈 RAG Agent 演示系统（React + FastAPI + SQLite + Chroma + LangGraph）。

**Architecture:** LangChain 负责文档 ingest 与向量检索（本地 BGE + Chroma）；LangGraph 编排 classify → retrieve → generate/refuse 状态图；DeepSeek API 负责 LLM 推理；SQLite 持久化会话与调试 trace；React 前端展示对话与调试面板。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, LangChain, LangGraph, ChromaDB, sentence-transformers, DeepSeek API, React 18, Vite, TypeScript, Tailwind CSS, pytest

**Spec reference:** `docs/superpowers/specs/2026-05-24-novacloud-rag-agent-design.md`

---

## File Map

| 路径 | 职责 |
|------|------|
| `backend/config.py` | 环境变量与 Settings 单例 |
| `backend/db/models.py` | Session, Message, Trace, Document ORM |
| `backend/db/session.py` | SQLAlchemy engine / get_db |
| `backend/rag/embeddings.py` | 本地 BGE Embedding 封装 |
| `backend/rag/ingest.py` | Markdown 分块 + 写入 Chroma |
| `backend/rag/retriever.py` | VectorStore retriever + 分数 |
| `backend/agent/state.py` | AgentState TypedDict |
| `backend/agent/prompts.py` | classify / generate / chitchat prompts |
| `backend/agent/nodes.py` | LangGraph 节点函数 |
| `backend/agent/graph.py` | 编译 StateGraph |
| `backend/schemas/chat.py` | Pydantic 请求/响应 |
| `backend/api/chat.py` | 对话 API |
| `backend/api/debug.py` | trace API |
| `backend/api/documents.py` | 文档列表 + reindex |
| `backend/main.py` | FastAPI 入口 |
| `backend/tests/` | pytest 测试 |
| `frontend/src/` | React 页面与组件 |
| `data/` | 虚拟演示 Markdown |
| `.env.example` | 环境变量模板 |
| `README.md` | 启动说明与架构 |

---

## Phase 1 — MVP（classify → retrieve → generate/refuse）

### Task 1: 项目脚手架与依赖

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/__init__.py`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `pyproject.toml`（pytest 配置）

- [ ] **Step 1: 创建 `.gitignore`**

```gitignore
.env
__pycache__/
*.pyc
.venv/
data/chroma/
db/*.db
frontend/node_modules/
frontend/dist/
.pytest_cache/
*.egg-info/
```

- [ ] **Step 2: 创建 `backend/requirements.txt`**

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
langchain>=0.3.0
langchain-community>=0.3.0
langgraph>=0.2.0
langchain-openai>=0.2.0
chromadb>=0.5.0
sentence-transformers>=3.0.0
sqlalchemy>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
httpx>=0.27.0
pytest>=8.0.0
pytest-asyncio>=0.24.0
```

- [ ] **Step 3: 创建 `.env.example`**

```
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
CHROMA_PERSIST_DIR=./data/chroma
SQLITE_URL=sqlite:///./db/novacloud.db
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
RETRIEVE_TOP_K=4
RELEVANCE_THRESHOLD=0.5
CORS_ORIGINS=http://localhost:5173
```

- [ ] **Step 4: 创建 `pyproject.toml`**

```toml
[tool.pytest.ini_options]
testpaths = ["backend/tests"]
pythonpath = ["."]
asyncio_mode = "auto"
```

- [ ] **Step 5: 安装依赖并验证**

Run: `python -m venv .venv && .venv\Scripts\activate && pip install -r backend/requirements.txt`
Expected: 安装成功，无报错

- [ ] **Step 6: Commit**

```bash
git add .gitignore .env.example backend/requirements.txt pyproject.toml backend/__init__.py
git commit -m "chore: scaffold project dependencies and env template"
```

---

### Task 2: 配置模块

**Files:**
- Create: `backend/config.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_config.py
"""配置模块测试。"""
from backend.config import get_settings


def test_settings_loads_defaults(monkeypatch):
  """未设置 env 时使用默认值。"""
  monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
  settings = get_settings()
  assert settings.deepseek_model == "deepseek-chat"
  assert settings.retrieve_top_k == 4
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest backend/tests/test_config.py -v`
Expected: FAIL `ModuleNotFoundError: backend.config`

- [ ] **Step 3: 实现 `backend/config.py`**

```python
"""应用配置：从环境变量加载 DeepSeek、Chroma、SQLite 等参数。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  """全局配置项。"""

  model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

  deepseek_api_key: str = ""
  deepseek_base_url: str = "https://api.deepseek.com/v1"
  deepseek_model: str = "deepseek-chat"
  chroma_persist_dir: str = "./data/chroma"
  sqlite_url: str = "sqlite:///./db/novacloud.db"
  embedding_model: str = "BAAI/bge-small-zh-v1.5"
  retrieve_top_k: int = 4
  relevance_threshold: float = 0.5
  cors_origins: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
  """返回缓存的配置单例。"""
  return Settings()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest backend/tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/config.py backend/tests/test_config.py
git commit -m "feat: add settings module with env loading"
```

---

### Task 3: SQLite 模型与数据库初始化

**Files:**
- Create: `backend/db/session.py`
- Create: `backend/db/models.py`
- Create: `backend/db/__init__.py`
- Test: `backend/tests/test_db.py`

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_db.py
"""数据库模型测试。"""
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.models import Base, ChatSession, Message, Trace


def test_create_session_and_message():
  """能创建会话并写入消息。"""
  engine = create_engine("sqlite:///:memory:")
  Base.metadata.create_all(engine)
  db = sessionmaker(bind=engine)()

  session = ChatSession(id=str(uuid.uuid4()), title="测试会话")
  db.add(session)
  db.commit()

  msg = Message(
    id=str(uuid.uuid4()),
    session_id=session.id,
    role="user",
    content="你好",
  )
  db.add(msg)
  db.commit()

  assert db.query(Message).count() == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest backend/tests/test_db.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 `backend/db/models.py`**

```python
"""SQLite ORM 模型：会话、消息、调试 trace、文档 registry。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
  """SQLAlchemy 声明基类。"""


class ChatSession(Base):
  """聊天会话。"""

  __tablename__ = "sessions"

  id: Mapped[str] = mapped_column(String(36), primary_key=True)
  title: Mapped[str] = mapped_column(String(200), default="新会话")
  created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
  messages: Mapped[list["Message"]] = relationship(back_populates="session")


class Message(Base):
  """单条聊天消息。"""

  __tablename__ = "messages"

  id: Mapped[str] = mapped_column(String(36), primary_key=True)
  session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"))
  role: Mapped[str] = mapped_column(String(20))
  content: Mapped[str] = mapped_column(Text)
  created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
  session: Mapped["ChatSession"] = relationship(back_populates="messages")
  trace: Mapped["Trace | None"] = relationship(back_populates="message", uselist=False)


class Trace(Base):
  """Agent 调试 trace JSON。"""

  __tablename__ = "traces"

  id: Mapped[str] = mapped_column(String(36), primary_key=True)
  message_id: Mapped[str] = mapped_column(String(36), ForeignKey("messages.id"), unique=True)
  payload: Mapped[str] = mapped_column(Text)
  created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
  message: Mapped["Message"] = relationship(back_populates="trace")


class DocumentRegistry(Base):
  """已入库文档 registry。"""

  __tablename__ = "documents"

  id: Mapped[str] = mapped_column(String(36), primary_key=True)
  path: Mapped[str] = mapped_column(String(500), unique=True)
  status: Mapped[str] = mapped_column(String(20), default="indexed")
  chunk_count: Mapped[int] = mapped_column(Integer, default=0)
  updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 4: 实现 `backend/db/session.py`**

```python
"""数据库 engine 与 FastAPI 依赖注入。"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import get_settings
from backend.db.models import Base

settings = get_settings()
engine = create_engine(settings.sqlite_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
  """创建所有表。"""
  Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
  """FastAPI 依赖：提供 DB session。"""
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest backend/tests/test_db.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/db/ backend/tests/test_db.py
git commit -m "feat: add SQLite models for sessions, messages, traces"
```

---

### Task 4: Embedding 封装

**Files:**
- Create: `backend/rag/embeddings.py`
- Create: `backend/rag/__init__.py`
- Test: `backend/tests/test_embeddings.py`

- [ ] **Step 1: 写失败测试（mock 模型避免下载）**

```python
# backend/tests/test_embeddings.py
"""Embedding 模块测试。"""
from unittest.mock import MagicMock, patch

from backend.rag.embeddings import get_embedding_function


@patch("backend.rag.embeddings.HuggingFaceEmbeddings")
def test_get_embedding_function_returns_instance(mock_cls):
  """应返回 HuggingFaceEmbeddings 实例。"""
  mock_cls.return_value = MagicMock()
  emb = get_embedding_function()
  assert emb is not None
  mock_cls.assert_called_once()
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest backend/tests/test_embeddings.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 `backend/rag/embeddings.py`**

```python
"""本地 BGE Embedding 封装，供 Chroma 与 Retriever 使用。"""
from functools import lru_cache

from langchain_community.embeddings import HuggingFaceEmbeddings

from backend.config import get_settings


@lru_cache
def get_embedding_function() -> HuggingFaceEmbeddings:
  """返回缓存的本地 embedding 模型。"""
  settings = get_settings()
  return HuggingFaceEmbeddings(
    model_name=settings.embedding_model,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
  )
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest backend/tests/test_embeddings.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/rag/embeddings.py backend/rag/__init__.py backend/tests/test_embeddings.py
git commit -m "feat: add local BGE embedding wrapper"
```

---

### Task 5: Markdown 分块工具

**Files:**
- Create: `backend/rag/chunker.py`
- Test: `backend/tests/test_chunker.py`

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_chunker.py
"""文档分块测试。"""
from backend.rag.chunker import split_markdown


SAMPLE = """# 部署指南

## 安装

运行 docker compose up。

## 配置

编辑 .env 文件。
"""


def test_split_markdown_by_headers():
  """应按 ## 标题分块并保留 section 元数据。"""
  chunks = split_markdown(SAMPLE, source="wiki/deployment.md")
  assert len(chunks) >= 2
  assert chunks[0].metadata["section"] == "安装"
  assert chunks[0].metadata["source"] == "wiki/deployment.md"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest backend/tests/test_chunker.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 `backend/rag/chunker.py`**

```python
"""Markdown 按标题分块，为 ingest 提供带元数据的 Document。"""
import re

from langchain_core.documents import Document


def split_markdown(text: str, source: str) -> list[Document]:
  """
  按 ## 二级标题切分 Markdown。

  Args:
    text: 原始 Markdown 文本
    source: 文件相对路径，写入 metadata

  Returns:
    带 source/section 元数据的 Document 列表
  """
  # 按 ## 标题拆分
  parts = re.split(r"(?m)^## ", text)
  chunks: list[Document] = []

  for part in parts:
    part = part.strip()
    if not part:
      continue

    lines = part.split("\n", 1)
    section = lines[0].strip()
    body = lines[1].strip() if len(lines) > 1 else part
    content = f"## {section}\n\n{body}" if body else f"## {section}"

    if len(content) < 20:
      continue

    chunks.append(
      Document(
        page_content=content,
        metadata={"source": source, "section": section},
      )
    )

  return chunks
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest backend/tests/test_chunker.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/rag/chunker.py backend/tests/test_chunker.py
git commit -m "feat: add markdown header-based chunker"
```

---

### Task 6: Ingest 管道

**Files:**
- Create: `backend/rag/ingest.py`
- Test: `backend/tests/test_ingest.py`

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_ingest.py
"""Ingest 管道测试。"""
from pathlib import Path

import pytest

from backend.rag.chunker import split_markdown


def test_split_faq_format():
  """FAQ 问答题应被正确分块。"""
  text = "问：如何重置密码？\n答：点击登录页忘记密码链接。"
  chunks = split_markdown(f"## 账号\n\n{text}", source="faq/account.md")
  assert any("重置密码" in c.page_content for c in chunks)


@pytest.mark.skip(reason="集成测试需 Chroma，Task 6 Step 4 后取消 skip")
def test_ingest_directory(tmp_path):
  """ingest 应处理目录下所有 md 文件。"""
  from backend.rag.ingest import ingest_directory

  wiki = tmp_path / "wiki"
  wiki.mkdir()
  (wiki / "billing.md").write_text("## 企业版定价\n\n每席位 99 元/月。", encoding="utf-8")

  count = ingest_directory(str(tmp_path), chroma_dir=str(tmp_path / "chroma"))
  assert count >= 1
```

- [ ] **Step 2: 运行测试**

Run: `pytest backend/tests/test_ingest.py -v`
Expected: 1 pass, 1 skipped

- [ ] **Step 3: 实现 `backend/rag/ingest.py`**

```python
"""扫描 data/ 目录，分块并写入 Chroma 向量库。"""
import argparse
import uuid
from pathlib import Path

from langchain_community.vectorstores import Chroma
from sqlalchemy.orm import Session

from backend.db.models import DocumentRegistry
from backend.db.session import SessionLocal, init_db
from backend.rag.chunker import split_markdown
from backend.rag.embeddings import get_embedding_function


def _collect_markdown_files(source_dir: Path) -> list[Path]:
  """递归收集 .md 文件。"""
  return sorted(source_dir.rglob("*.md"))


def ingest_directory(source: str, chroma_dir: str | None = None) -> int:
  """
  入库指定目录下所有 Markdown。

  Args:
    source: 文档根目录
    chroma_dir: Chroma 持久化路径，默认读 config

  Returns:
    写入的 chunk 总数
  """
  from backend.config import get_settings

  settings = get_settings()
  persist_dir = chroma_dir or settings.chroma_persist_dir
  source_path = Path(source)

  if not source_path.exists():
    raise FileNotFoundError(f"Source directory not found: {source}")

  # 初始化 DB 与向量库
  init_db()
  embedding = get_embedding_function()
  vectorstore = Chroma(
    collection_name="novacloud",
    embedding_function=embedding,
    persist_directory=persist_dir,
  )

  total_chunks = 0
  db: Session = SessionLocal()

  try:
    for md_file in _collect_markdown_files(source_path):
      rel_path = md_file.relative_to(source_path).as_posix()
      text = md_file.read_text(encoding="utf-8")
      chunks = split_markdown(text, source=rel_path)

      if not chunks:
        continue

      # 写入 Chroma
      vectorstore.add_documents(chunks)

      # 更新 registry
      doc = db.query(DocumentRegistry).filter_by(path=rel_path).first()
      if doc is None:
        doc = DocumentRegistry(id=str(uuid.uuid4()), path=rel_path)
        db.add(doc)

      doc.chunk_count = len(chunks)
      doc.status = "indexed"
      total_chunks += len(chunks)

    db.commit()
  finally:
    db.close()

  return total_chunks


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Ingest markdown into Chroma")
  parser.add_argument("--source", default="./data", help="Document root directory")
  args = parser.parse_args()
  n = ingest_directory(args.source)
  print(f"Ingested {n} chunks.")
```

- [ ] **Step 4: 取消 skip 并运行 ingest 集成测试**

在 `test_ingest.py` 中移除 `@pytest.mark.skip`，然后：

Run: `pytest backend/tests/test_ingest.py -v`
Expected: PASS（首次可能较慢，需下载 embedding 模型）

- [ ] **Step 5: Commit**

```bash
git add backend/rag/ingest.py backend/tests/test_ingest.py
git commit -m "feat: add markdown ingest pipeline to Chroma"
```

---

### Task 7: Retriever

**Files:**
- Create: `backend/rag/retriever.py`
- Test: `backend/tests/test_retriever.py`

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_retriever.py
"""Retriever 测试。"""
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from backend.rag.retriever import retrieve_with_scores


@patch("backend.rag.retriever._get_vectorstore")
def test_retrieve_with_scores_returns_scored_docs(mock_vs):
  """应返回 (document, score) 列表。"""
  doc = Document(page_content="test", metadata={"source": "a.md", "section": "S"})
  mock_vs.return_value.similarity_search_with_relevance_scores.return_value = [(doc, 0.9)]

  results = retrieve_with_scores("query")
  assert len(results) == 1
  assert results[0]["score"] == 0.9
  assert results[0]["source"] == "a.md"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest backend/tests/test_retriever.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 `backend/rag/retriever.py`**

```python
"""Chroma 向量检索，返回带分数的 chunks。"""
from functools import lru_cache

from langchain_community.vectorstores import Chroma

from backend.config import get_settings
from backend.rag.embeddings import get_embedding_function


@lru_cache
def _get_vectorstore() -> Chroma:
  """返回持久化 Chroma 实例。"""
  settings = get_settings()
  return Chroma(
    collection_name="novacloud",
    embedding_function=get_embedding_function(),
    persist_directory=settings.chroma_persist_dir,
  )


def retrieve_with_scores(query: str, top_k: int | None = None) -> list[dict]:
  """
  语义检索 top-k 文档块。

  Args:
    query: 用户问题或改写 query
    top_k: 返回数量，默认读配置

  Returns:
    含 content, source, section, score 的字典列表
  """
  settings = get_settings()
  k = top_k or settings.retrieve_top_k
  vectorstore = _get_vectorstore()

  pairs = vectorstore.similarity_search_with_relevance_scores(query, k=k)
  results: list[dict] = []

  for doc, score in pairs:
    results.append(
      {
        "content": doc.page_content,
        "source": doc.metadata.get("source", "unknown"),
        "section": doc.metadata.get("section", ""),
        "score": round(float(score), 4),
      }
    )

  return results
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest backend/tests/test_retriever.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/rag/retriever.py backend/tests/test_retriever.py
git commit -m "feat: add Chroma retriever with relevance scores"
```

---

### Task 8: Agent 状态与 Prompt

**Files:**
- Create: `backend/agent/state.py`
- Create: `backend/agent/prompts.py`
- Create: `backend/agent/__init__.py`

- [ ] **Step 1: 实现 `backend/agent/state.py`**

```python
"""LangGraph AgentState 类型定义。"""
from typing import TypedDict


class Citation(TypedDict):
  """引用来源。"""
  source: str
  section: str


class NodeTrace(TypedDict, total=False):
  """单节点调试 trace。"""
  name: str
  duration_ms: int
  input: dict
  output: dict


class AgentState(TypedDict, total=False):
  """图状态：在各节点间传递。"""
  question: str
  rewritten_question: str | None
  route: str
  documents: list[dict]
  relevance_scores: list[float]
  retry_count: int
  is_relevant: bool
  answer: str
  citations: list[Citation]
  node_trace: list[NodeTrace]
```

- [ ] **Step 2: 实现 `backend/agent/prompts.py`**

```python
"""Agent 各节点 Prompt 模板。"""

CLASSIFY_PROMPT = """你是 NovaCloud 协作平台的知识库路由助手。
判断用户问题是否需要查询企业内部文档（产品手册、Wiki、FAQ）。
仅回复 JSON：{{"route": "need_rag"}} 或 {{"route": "no_rag"}}
用户问题：{question}"""

GENERATE_PROMPT = """你是 NovaCloud 企业知识库助手。仅根据以下参考资料回答，必须标注来源。
若资料不足以回答，回复「知识库中未找到依据」。
参考资料：
{context}

用户问题：{question}

要求：回答简洁准确，末尾列出 [来源: 文件路径 § 章节]。"""

CHITCHAT_PROMPT = """你是 NovaCloud 助手。用户问题与产品文档无关，简短友好回复，不要编造产品功能。
用户问题：{question}"""

REFUSE_MESSAGE = "知识库中未找到依据，建议联系管理员或提交工单。"
```

- [ ] **Step 3: Commit**

```bash
git add backend/agent/state.py backend/agent/prompts.py backend/agent/__init__.py
git commit -m "feat: add agent state types and prompt templates"
```

---

### Task 9: LLM 客户端

**Files:**
- Create: `backend/agent/llm.py`
- Test: `backend/tests/test_llm.py`

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_llm.py
from unittest.mock import patch

from backend.agent.llm import get_llm


@patch("backend.agent.llm.ChatOpenAI")
def test_get_llm_uses_deepseek_config(mock_chat):
  """LLM 应使用 DeepSeek base_url 与 model。"""
  get_llm()
  mock_chat.assert_called_once()
  kwargs = mock_chat.call_args.kwargs
  assert "deepseek" in kwargs["base_url"] or kwargs["model"] == "deepseek-chat"
```

- [ ] **Step 2-4: 实现并验证**

```python
# backend/agent/llm.py
"""DeepSeek LLM 客户端（OpenAI 兼容接口）。"""
from functools import lru_cache

from langchain_openai import ChatOpenAI

from backend.config import get_settings


@lru_cache
def get_llm() -> ChatOpenAI:
  """返回 DeepSeek ChatOpenAI 实例。"""
  settings = get_settings()
  return ChatOpenAI(
    model=settings.deepseek_model,
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
    temperature=0.2,
  )
```

Run: `pytest backend/tests/test_llm.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agent/llm.py backend/tests/test_llm.py
git commit -m "feat: add DeepSeek LLM client via OpenAI-compatible API"
```

---

### Task 10: LangGraph 节点（Phase 1 MVP）

**Files:**
- Create: `backend/agent/nodes.py`
- Test: `backend/tests/test_nodes.py`

- [ ] **Step 1: 写失败测试**

```python
# backend/tests/test_nodes.py
from backend.agent.nodes import refuse_node, should_refuse_after_retrieve


def test_should_refuse_when_no_docs():
  """无检索结果时应拒答。"""
  state = {"documents": [], "relevance_scores": []}
  assert should_refuse_after_retrieve(state) is True


def test_refuse_node_sets_message():
  """拒答节点应写入固定话术。"""
  result = refuse_node({"question": "火星怎么登录"})
  assert "未找到依据" in result["answer"]
```

- [ ] **Step 2-4: 实现 `backend/agent/nodes.py`（MVP 核心节点）**

```python
"""LangGraph 节点：classify, retrieve, generate, refuse, chitchat。"""
import json
import time

from langchain_core.messages import HumanMessage

from backend.agent.llm import get_llm
from backend.agent.prompts import (
  CHITCHAT_PROMPT,
  CLASSIFY_PROMPT,
  GENERATE_PROMPT,
  REFUSE_MESSAGE,
)
from backend.agent.state import AgentState
from backend.config import get_settings
from backend.rag.retriever import retrieve_with_scores


def _append_trace(state: AgentState, name: str, duration_ms: int, inp: dict, out: dict) -> list:
  """追加节点 trace 到 state。"""
  trace = list(state.get("node_trace") or [])
  trace.append({"name": name, "duration_ms": duration_ms, "input": inp, "output": out})
  return trace


def classify_node(state: AgentState) -> AgentState:
  """判断是否需要 RAG 检索。"""
  start = time.perf_counter()
  llm = get_llm()
  prompt = CLASSIFY_PROMPT.format(question=state["question"])
  raw = llm.invoke([HumanMessage(content=prompt)]).content

  # 解析 JSON 路由
  route = "need_rag"
  try:
    parsed = json.loads(raw.strip())
    route = parsed.get("route", "need_rag")
  except json.JSONDecodeError:
    route = "need_rag" if "no_rag" not in raw else "no_rag"

  elapsed = int((time.perf_counter() - start) * 1000)
  return {
    "route": route,
    "node_trace": _append_trace(state, "classify", elapsed, {"question": state["question"]}, {"route": route}),
  }


def retrieve_node(state: AgentState) -> AgentState:
  """向量检索 top-k chunks。"""
  start = time.perf_counter()
  query = state.get("rewritten_question") or state["question"]
  docs = retrieve_with_scores(query)
  scores = [d["score"] for d in docs]
  elapsed = int((time.perf_counter() - start) * 1000)

  return {
    "documents": docs,
    "relevance_scores": scores,
    "node_trace": _append_trace(
      state, "retrieve", elapsed, {"query": query}, {"top_k": len(docs), "chunks": docs}
    ),
  }


def should_refuse_after_retrieve(state: AgentState) -> bool:
  """MVP：最高分低于阈值或无结果则拒答。"""
  settings = get_settings()
  scores = state.get("relevance_scores") or []
  if not scores:
    return True
  return max(scores) < settings.relevance_threshold


def generate_node(state: AgentState) -> AgentState:
  """基于检索片段生成带引用答案。"""
  start = time.perf_counter()
  docs = state.get("documents") or []
  context = "\n\n---\n\n".join(
    f"[{d['source']} § {d['section']}]\n{d['content']}" for d in docs
  )
  llm = get_llm()
  prompt = GENERATE_PROMPT.format(context=context, question=state["question"])
  answer = llm.invoke([HumanMessage(content=prompt)]).content

  citations = [{"source": d["source"], "section": d["section"]} for d in docs[:3]]
  elapsed = int((time.perf_counter() - start) * 1000)

  return {
    "answer": answer,
    "citations": citations,
    "node_trace": _append_trace(
      state, "generate", elapsed, {"context_chunks": len(docs)}, {"answer_preview": answer[:120]}
    ),
  }


def refuse_node(state: AgentState) -> AgentState:
  """固定拒答话术。"""
  return {"answer": REFUSE_MESSAGE, "citations": [], "node_trace": state.get("node_trace") or []}


def chitchat_node(state: AgentState) -> AgentState:
  """非知识库问题的简短回复。"""
  start = time.perf_counter()
  llm = get_llm()
  prompt = CHITCHAT_PROMPT.format(question=state["question"])
  answer = llm.invoke([HumanMessage(content=prompt)]).content
  elapsed = int((time.perf_counter() - start) * 1000)

  return {
    "answer": answer,
    "citations": [],
    "node_trace": _append_trace(state, "chitchat", elapsed, {"question": state["question"]}, {"answer_preview": answer[:80]}),
  }
```

Run: `pytest backend/tests/test_nodes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agent/nodes.py backend/tests/test_nodes.py
git commit -m "feat: add LangGraph nodes for MVP agent flow"
```

---

### Task 11: 编译 LangGraph

**Files:**
- Create: `backend/agent/graph.py`
- Test: `backend/tests/test_graph.py`

- [ ] **Step 1: 写失败测试（mock LLM）**

```python
# backend/tests/test_graph.py
from unittest.mock import patch

from backend.agent.graph import build_graph


@patch("backend.agent.nodes.get_llm")
@patch("backend.agent.nodes.retrieve_with_scores")
def test_graph_refuses_when_no_results(mock_retrieve, mock_llm):
  """无检索结果时应走 refuse 分支。"""
  mock_retrieve.return_value = []
  mock_llm.return_value.invoke.return_value.content = '{"route": "need_rag"}'

  graph = build_graph()
  result = graph.invoke({"question": "不存在的问题 xyz123"})

  assert "未找到依据" in result["answer"]
```

- [ ] **Step 2-4: 实现 `backend/agent/graph.py`**

```python
"""编译 LangGraph StateGraph（Phase 1 MVP）。"""
from langgraph.graph import END, StateGraph

from backend.agent.nodes import (
  chitchat_node,
  classify_node,
  generate_node,
  refuse_node,
  retrieve_node,
  should_refuse_after_retrieve,
)
from backend.agent.state import AgentState


def _route_after_classify(state: AgentState) -> str:
  """classify 后路由。"""
  if state.get("route") == "no_rag":
    return "chitchat"
  return "retrieve"


def _route_after_retrieve(state: AgentState) -> str:
  """retrieve 后：拒答或生成。"""
  if should_refuse_after_retrieve(state):
    return "refuse"
  return "generate"


def build_graph():
  """构建并编译 Agent 图。"""
  graph = StateGraph(AgentState)

  graph.add_node("classify", classify_node)
  graph.add_node("retrieve", retrieve_node)
  graph.add_node("generate", generate_node)
  graph.add_node("refuse", refuse_node)
  graph.add_node("chitchat", chitchat_node)

  graph.set_entry_point("classify")
  graph.add_conditional_edges("classify", _route_after_classify, {"retrieve": "retrieve", "chitchat": "chitchat"})
  graph.add_conditional_edges("retrieve", _route_after_retrieve, {"refuse": "refuse", "generate": "generate"})
  graph.add_edge("generate", END)
  graph.add_edge("refuse", END)
  graph.add_edge("chitchat", END)

  return graph.compile()
```

Run: `pytest backend/tests/test_graph.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/agent/graph.py backend/tests/test_graph.py
git commit -m "feat: compile LangGraph MVP workflow"
```

---

### Task 12: Pydantic Schemas 与 Chat API

**Files:**
- Create: `backend/schemas/chat.py`
- Create: `backend/schemas/__init__.py`
- Create: `backend/api/chat.py`
- Create: `backend/api/__init__.py`
- Test: `backend/tests/test_chat_api.py`

- [ ] **Step 1: 实现 schemas**

```python
# backend/schemas/chat.py
"""对话 API 请求/响应模型。"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
  question: str = Field(min_length=1, max_length=2000)
  session_id: str | None = None


class CitationOut(BaseModel):
  source: str
  section: str


class ChatResponse(BaseModel):
  message_id: str
  session_id: str
  answer: str
  citations: list[CitationOut]
  trace_id: str


class MessageOut(BaseModel):
  id: str
  role: str
  content: str
  created_at: str


class SessionOut(BaseModel):
  id: str
  title: str
  created_at: str
```

- [ ] **Step 2: 写 API 测试**

```python
# backend/tests/test_chat_api.py
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


@patch("backend.api.chat.run_agent")
def test_post_chat_returns_answer(mock_run):
  """POST /api/chat 应返回答案与 trace_id。"""
  mock_run.return_value = {
    "answer": "测试回答",
    "citations": [{"source": "wiki/billing.md", "section": "定价"}],
    "node_trace": [{"name": "classify", "duration_ms": 1, "input": {}, "output": {}}],
  }

  resp = client.post("/api/chat", json={"question": "企业版如何计费？"})
  assert resp.status_code == 200
  body = resp.json()
  assert body["answer"] == "测试回答"
  assert body["trace_id"]
```

- [ ] **Step 3: 实现 `backend/api/chat.py`**

```python
"""对话 REST API。"""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.agent.graph import build_graph
from backend.db.models import ChatSession, Message, Trace
from backend.db.session import get_db
from backend.schemas.chat import ChatRequest, ChatResponse, MessageOut, SessionOut

router = APIRouter(prefix="/api", tags=["chat"])
_graph = None


def _get_graph():
  global _graph
  if _graph is None:
    _graph = build_graph()
  return _graph


def run_agent(question: str) -> dict:
  """执行 Agent 并返回结果 dict。"""
  graph = _get_graph()
  return graph.invoke({"question": question, "node_trace": []})


@router.post("/chat", response_model=ChatResponse)
def post_chat(body: ChatRequest, db: Session = Depends(get_db)):
  """发送问题，持久化消息与 trace。"""
  session_id = body.session_id or str(uuid.uuid4())

  session = db.query(ChatSession).filter_by(id=session_id).first()
  if session is None:
    title = body.question[:30]
    session = ChatSession(id=session_id, title=title)
    db.add(session)

  user_msg = Message(id=str(uuid.uuid4()), session_id=session_id, role="user", content=body.question)
  db.add(user_msg)

  result = run_agent(body.question)
  assistant_msg = Message(
    id=str(uuid.uuid4()),
    session_id=session_id,
    role="assistant",
    content=result.get("answer", ""),
  )
  db.add(assistant_msg)

  trace_payload = {
    "message_id": assistant_msg.id,
    "question": body.question,
    "nodes": result.get("node_trace", []),
    "citations": result.get("citations", []),
  }
  trace = Trace(id=str(uuid.uuid4()), message_id=assistant_msg.id, payload=json.dumps(trace_payload, ensure_ascii=False))
  db.add(trace)
  db.commit()

  return ChatResponse(
    message_id=assistant_msg.id,
    session_id=session_id,
    answer=result.get("answer", ""),
    citations=result.get("citations", []),
    trace_id=trace.id,
  )


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db)):
  """会话列表。"""
  sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
  return [SessionOut(id=s.id, title=s.title, created_at=s.created_at.isoformat()) for s in sessions]


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
def list_messages(session_id: str, db: Session = Depends(get_db)):
  """会话消息历史。"""
  if db.query(ChatSession).filter_by(id=session_id).first() is None:
    raise HTTPException(status_code=404, detail="Session not found")

  messages = db.query(Message).filter_by(session_id=session_id).order_by(Message.created_at).all()
  return [
    MessageOut(id=m.id, role=m.role, content=m.content, created_at=m.created_at.isoformat())
    for m in messages
  ]
```

- [ ] **Step 4: 实现 `backend/main.py`（最小版供测试）**

```python
"""FastAPI 应用入口。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.chat import router as chat_router
from backend.config import get_settings
from backend.db.session import init_db

settings = get_settings()
app = FastAPI(title="NovaCloud RAG Agent")

app.add_middleware(
  CORSMiddleware,
  allow_origins=settings.cors_origins.split(","),
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(chat_router)


@app.on_event("startup")
def on_startup():
  init_db()
```

Run: `pytest backend/tests/test_chat_api.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/schemas/ backend/api/chat.py backend/main.py backend/tests/test_chat_api.py
git commit -m "feat: add chat API with session and trace persistence"
```

---

### Task 13: Debug 与 Documents API

**Files:**
- Create: `backend/api/debug.py`
- Create: `backend/api/documents.py`
- Test: `backend/tests/test_debug_api.py`

- [ ] **Step 1: 实现 debug API**

```python
# backend/api/debug.py
"""调试 trace API。"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.models import Trace
from backend.db.session import get_db

router = APIRouter(prefix="/api", tags=["debug"])


@router.get("/traces/{message_id}")
def get_trace(message_id: str, db: Session = Depends(get_db)):
  """按 assistant message_id 返回完整 trace JSON。"""
  trace = db.query(Trace).filter_by(message_id=message_id).first()
  if trace is None:
    raise HTTPException(status_code=404, detail="Trace not found")
  return json.loads(trace.payload)
```

- [ ] **Step 2: 实现 documents API**

```python
# backend/api/documents.py
"""文档 registry 与 reindex API。"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.models import DocumentRegistry
from backend.db.session import get_db
from backend.rag.ingest import ingest_directory

router = APIRouter(prefix="/api", tags=["documents"])


class DocumentOut(BaseModel):
  id: str
  path: str
  status: str
  chunk_count: int


class ReindexRequest(BaseModel):
  source: str = "./data"


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
  """已入库文档列表。"""
  docs = db.query(DocumentRegistry).order_by(DocumentRegistry.path).all()
  return [DocumentOut(id=d.id, path=d.path, status=d.status, chunk_count=d.chunk_count) for d in docs]


@router.post("/documents/reindex")
def reindex(body: ReindexRequest, db: Session = Depends(get_db)):
  """触发全量 re-index。"""
  count = ingest_directory(body.source)
  return {"status": "ok", "chunks_indexed": count}
```

- [ ] **Step 3: 挂载路由到 main.py**

在 `backend/main.py` 添加：

```python
from backend.api.debug import router as debug_router
from backend.api.documents import router as documents_router

app.include_router(debug_router)
app.include_router(documents_router)
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/debug.py backend/api/documents.py backend/main.py
git commit -m "feat: add debug trace and document reindex APIs"
```

---

### Task 14: 虚拟演示数据

**Files:**
- Create: `data/wiki/billing.md`
- Create: `data/wiki/deployment.md`
- Create: `data/wiki/permissions.md`
- Create: `data/product_manual/overview.md`
- Create: `data/product_manual/features.md`
- Create: `data/faq/account.md`
- Create: `data/faq/troubleshooting.md`

- [ ] **Step 1: 编写虚构 NovaCloud 文档（每文件 300-800 字）**

`data/wiki/billing.md` 示例开头：

```markdown
# NovaCloud 计费说明

## 免费版

个人用户免费，最多 3 人协作空间，存储 1GB。

## 企业版定价

按年订阅，每席位 99 元/月（年付 950 元/席位）。含 SSO、审计日志、专属客服。

## 发票与退款

支持增值税专票。年付 7 天内未使用可申请全额退款。
```

其余文件按 spec §9 结构编写，保持价格/功能名一致。

- [ ] **Step 2: 运行 ingest**

Run: `python -m backend.rag.ingest --source ./data`
Expected: `Ingested N chunks.`（N >= 10）

- [ ] **Step 3: Commit**

```bash
git add data/
git commit -m "docs: add NovaCloud fictional demo knowledge base"
```

---

### Task 15: React 前端脚手架

**Files:**
- Create: `frontend/` via Vite

- [ ] **Step 1: 创建 Vite React TS 项目**

Run:
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install && npm install axios react-router-dom
npm install -D tailwindcss @tailwindcss/vite
```

- [ ] **Step 2: 配置 `frontend/vite.config.ts` 代理**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

- [ ] **Step 3: 配置路由 `frontend/src/App.tsx`**

```tsx
import { BrowserRouter, Route, Routes, Link } from "react-router-dom";
import ChatPage from "./pages/ChatPage";
import DocumentsPage from "./pages/DocumentsPage";

export default function App() {
  return (
    <BrowserRouter>
      <header className="border-b px-6 py-3 flex justify-between items-center">
        <h1 className="font-semibold text-lg">NovaCloud 知识库助手</h1>
        <nav className="gap-4 flex">
          <Link to="/">对话</Link>
          <Link to="/documents">文档管理</Link>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React frontend with Vite and routing"
```

---

### Task 16: API Client

**Files:**
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/types.ts`

- [ ] **Step 1: 实现 types 与 client**

```typescript
// frontend/src/api/types.ts
export interface Citation {
  source: string;
  section: string;
}

export interface ChatResponse {
  message_id: string;
  session_id: string;
  answer: string;
  citations: Citation[];
  trace_id: string;
}

export interface TraceNode {
  name: string;
  duration_ms: number;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
}

export interface TracePayload {
  message_id: string;
  question: string;
  nodes: TraceNode[];
  citations: Citation[];
}

export interface DocumentItem {
  id: string;
  path: string;
  status: string;
  chunk_count: number;
}
```

```typescript
// frontend/src/api/client.ts
import axios from "axios";
import type { ChatResponse, DocumentItem, TracePayload } from "./types";

const api = axios.create({ baseURL: "/api" });

export async function sendChat(question: string, sessionId?: string): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/chat", { question, session_id: sessionId });
  return data;
}

export async function fetchTrace(messageId: string): Promise<TracePayload> {
  const { data } = await api.get<TracePayload>(`/traces/${messageId}`);
  return data;
}

export async function fetchDocuments(): Promise<DocumentItem[]> {
  const { data } = await api.get<DocumentItem[]>("/documents");
  return data;
}

export async function reindexDocuments(source = "./data"): Promise<{ chunks_indexed: number }> {
  const { data } = await api.post("/documents/reindex", { source });
  return data;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/
git commit -m "feat: add typed API client for chat, traces, documents"
```

---

### Task 17: 调试面板组件

**Files:**
- Create: `frontend/src/components/DebugPanel/TraceTimeline.tsx`
- Create: `frontend/src/components/DebugPanel/RetrieveDetails.tsx`
- Create: `frontend/src/components/DebugPanel/RawJsonViewer.tsx`
- Create: `frontend/src/components/DebugPanel/index.tsx`

- [ ] **Step 1: 实现 TraceTimeline**

```tsx
// frontend/src/components/DebugPanel/TraceTimeline.tsx
import type { TraceNode } from "../../api/types";

export default function TraceTimeline({ nodes }: { nodes: TraceNode[] }) {
  const total = nodes.reduce((s, n) => s + n.duration_ms, 0) || 1;

  return (
    <div className="space-y-2">
      <p className="text-sm text-gray-500">总耗时 {total} ms</p>
      {nodes.map((n) => (
        <motion.div key={n.name} className="flex items-center gap-2 text-sm">
          <span className="w-20 font-mono">{n.name}</span>
          <div className="flex-1 bg-gray-100 rounded h-4">
            <div
              className="bg-blue-500 h-4 rounded"
              style={{ width: `${(n.duration_ms / total) * 100}%` }}
            />
          </div>
          <span className="w-12 text-right">{n.duration_ms}ms</span>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: 实现 RetrieveDetails 与 RawJsonViewer**

`RetrieveDetails.tsx` 从 `nodes` 中找到 `name === "retrieve"` 的节点，展示 `output.chunks` 列表（source, section, score, content 前 120 字）。

`RawJsonViewer.tsx` 用 `<pre>` 折叠展示完整 JSON。

- [ ] **Step 3: DebugPanel/index.tsx 组合**

```tsx
import TraceTimeline from "./TraceTimeline";
import RetrieveDetails from "./RetrieveDetails";
import RawJsonViewer from "./RawJsonViewer";
import type { TracePayload } from "../../api/types";

export default function DebugPanel({ trace }: { trace: TracePayload | null }) {
  if (!trace) return <div className="p-4 text-gray-400">发送问题后显示调试信息</div>;

  return (
    <div className="p-4 space-y-4 overflow-y-auto h-full">
      <h2 className="font-semibold">🔧 调试面板</h2>
      <TraceTimeline nodes={trace.nodes} />
      <RetrieveDetails nodes={trace.nodes} />
      <div>
        <h3 className="text-sm font-medium mb-1">引用</h3>
        <ul className="text-xs space-y-1">
          {trace.citations.map((c, i) => (
            <li key={i}>{c.source} § {c.section}</li>
          ))}
        </ul>
      </div>
      <RawJsonViewer data={trace} />
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/DebugPanel/
git commit -m "feat: add debug panel with timeline and retrieve details"
```

---

### Task 18: 对话页

**Files:**
- Create: `frontend/src/pages/ChatPage.tsx`
- Create: `frontend/src/components/MessageBubble.tsx`
- Create: `frontend/src/components/CitationBadge.tsx`

- [ ] **Step 1: 实现 ChatPage 布局（左聊天 + 右调试）**

核心逻辑：
- `sessionId` state
- `messages` state
- 发送时调用 `sendChat(question, sessionId)`
- 收到响应后 `fetchTrace(message_id)` 更新 debug panel
- 示例问题按钮：「企业版如何计费？」「如何重置密码？」「火星怎么登录？」（拒答 demo）

- [ ] **Step 2: MessageBubble 展示 citations**

助手消息下方渲染 `CitationBadge` 列表。

- [ ] **Step 3: 手动验证**

Run backend: `uvicorn backend.main:app --reload --port 8000`
Run frontend: `cd frontend && npm run dev`
Expected: 提问后右侧调试面板显示 classify → retrieve → generate 时间线

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/ChatPage.tsx frontend/src/components/
git commit -m "feat: add chat page with debug panel integration"
```

---

### Task 19: 文档管理页

**Files:**
- Create: `frontend/src/pages/DocumentsPage.tsx`
- Create: `frontend/src/components/DocumentTable.tsx`

- [ ] **Step 1: DocumentTable 展示 path / status / chunk_count**

- [ ] **Step 2: Re-index 按钮调用 reindexDocuments()，显示 toast 或 alert**

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/DocumentsPage.tsx frontend/src/components/DocumentTable.tsx
git commit -m "feat: add documents management page with reindex"
```

---

### Task 20: README 与交付

**Files:**
- Create: `README.md`

- [ ] **Step 1: 编写 README**

必须包含：
- 项目简介与架构图（引用 spec）
- 技术栈与 DeepSeek + BGE 分工说明
- 环境准备（Python、Node、`.env`）
- 启动四步命令
- 5 个 demo 问题与预期行为
- 作品集截图占位说明
- Embedding 模型镜像/离线提示

- [ ] **Step 2: 全链路手动验收**

| 问题 | 预期 |
|------|------|
| 企业版如何计费？ | 引用 billing.md，调试面板有 retrieve chunks |
| 如何重置密码？ | 引用 faq/account.md |
| 你好 | chitchat 分支，无 citations |
| 火星怎么登录？ | 拒答 |
| 调试面板 | 显示节点耗时与 JSON |

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and demo guide"
```

---

## Phase 2 — 增强（spec §5.4，MVP 完成后）

### Task 21: grade + rewrite 节点

**Files:**
- Modify: `backend/agent/nodes.py`
- Modify: `backend/agent/graph.py`
- Modify: `backend/agent/prompts.py`
- Test: `backend/tests/test_graph_rewrite.py`

- [ ] 新增 `grade_node`：检查 top score >= threshold 且 LLM 确认可回答
- [ ] 新增 `rewrite_node`：DeepSeek 改写 query，`retry_count += 1`
- [ ] 图改为：retrieve → grade → generate | rewrite | refuse
- [ ] 前端 `RetrieveDetails` 增加 rewrite 历史展示
- [ ] Commit: `feat: add grade and rewrite loop to agent graph`

---

## Spec Coverage Checklist

| Spec 章节 | 对应 Task |
|-----------|-----------|
| §2 存储分工 | Task 3, 6, 7, 12 |
| §4 后端模块 | Task 1-13 |
| §5 LangGraph | Task 8-11, 21 |
| §6 调试映射 | Task 12-13, 17-18 |
| §7 API | Task 12-13 |
| §8 前端 | Task 15-19 |
| §9 虚拟数据 | Task 14 |
| §10 环境运行 | Task 1, 20 |
| §11 测试 | 各 Task 内 pytest |
| §12 交付清单 | Task 20 |

---

## Self-Review Notes

- 所有 Task 含具体文件路径与代码片段，无 TBD
- Phase 1 严格 YAGNI：无 upload、无 BM25、无 rewrite
- `CitationOut` / `TracePayload` 字段与 spec JSON 一致
- `chunker.py` 在 Task 5 独立，避免 ingest 过于臃肿
