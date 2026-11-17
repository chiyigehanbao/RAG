"""扫描 data/ 目录或单文件，分块并写入 Chroma 向量库。"""
import argparse
import uuid
from pathlib import Path

import chromadb
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.db.models import DocumentRegistry
from backend.db.session import SessionLocal, init_db
from backend.rag.chunker import split_markdown
from backend.rag.bm25_store import rebuild as rebuild_bm25
from backend.rag.corpus import corpus_for_source
from backend.rag.embeddings import get_embedding_function


def _rebuild_bm25_from_chroma(vectorstore: Chroma) -> None:
    """从 Chroma 全量读取 chunk 并重建 BM25 索引。"""
    payload = vectorstore._collection.get(include=["documents", "metadatas"])
    docs = payload.get("documents") or []
    metas = payload.get("metadatas") or []
    chunks = [
        Document(page_content=content, metadata=meta or {})
        for content, meta in zip(docs, metas)
    ]
    rebuild_bm25(chunks)


def _tag_chunks(chunks: list[Document], source_key: str) -> list[Document]:
    """为每个 chunk 写入 corpus 元数据，供检索过滤。"""
    corpus = corpus_for_source(source_key)
    for doc in chunks:
        doc.metadata["corpus"] = corpus
    return chunks

COLLECTION_NAME = "novacloud"


def _collect_markdown_files(source_dir: Path) -> list[Path]:
    """递归收集 .md 文件。"""
    return sorted(source_dir.rglob("*.md"))


def _reset_collection(persist_dir: str, collection_name: str) -> None:
    """删除已有 collection，避免重复 ingest 产生重复向量。"""
    client = chromadb.PersistentClient(path=persist_dir)
    try:
        client.delete_collection(collection_name)
    except ValueError:
        pass


def _open_vectorstore(persist_dir: str) -> Chroma:
    """打开或创建 Chroma 向量库（不清库）。"""
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        persist_directory=persist_dir,
    )


def _delete_chunks_by_source(vectorstore: Chroma, source_key: str) -> None:
    """删除某来源文件在向量库中的旧 chunk。"""
    try:
        vectorstore._collection.delete(where={"source": source_key})
    except Exception:
        pass


def _upsert_registry(db: Session, source_key: str, chunk_count: int) -> None:
    """更新文档 registry 记录。"""
    doc = db.query(DocumentRegistry).filter_by(path=source_key).first()
    if doc is None:
        doc = DocumentRegistry(id=str(uuid.uuid4()), path=source_key)
        db.add(doc)
    doc.chunk_count = chunk_count
    doc.status = "indexed"


def ingest_file(file_path: Path, source_key: str, chroma_dir: str | None = None) -> int:
    """
    增量入库单个 Markdown（不清全库，先删同 source 旧向量）。

    Args:
        file_path: 磁盘上的 .md 绝对路径
        source_key: 写入 metadata 的 source，如 uploads/abc.md
        chroma_dir: Chroma 目录

    Returns:
        写入的 chunk 数
    """
    settings = get_settings()
    persist_dir = chroma_dir or settings.chroma_persist_dir

    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    text = file_path.read_text(encoding="utf-8")
    chunks: list[Document] = split_markdown(text, source=source_key)
    if not chunks:
        return 0
    chunks = _tag_chunks(chunks, source_key)

    init_db()
    vectorstore = _open_vectorstore(persist_dir)
    _delete_chunks_by_source(vectorstore, source_key)
    vectorstore.add_documents(chunks)
    _rebuild_bm25_from_chroma(vectorstore)

    db: Session = SessionLocal()
    try:
        _upsert_registry(db, source_key, len(chunks))
        db.commit()
    finally:
        db.close()

    return len(chunks)


def ingest_directory(source: str, chroma_dir: str | None = None) -> int:
    """
    全量入库指定目录下所有 Markdown（清库后重建）。

    Args:
        source: 文档根目录
        chroma_dir: Chroma 持久化路径，默认读 config

    Returns:
        写入的 chunk 总数
    """
    settings = get_settings()
    persist_dir = chroma_dir or settings.chroma_persist_dir
    source_path = Path(source)

    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source}")

    init_db()
    _reset_collection(persist_dir, COLLECTION_NAME)
    vectorstore = _open_vectorstore(persist_dir)

    total_chunks = 0
    db: Session = SessionLocal()

    try:
        for md_file in _collect_markdown_files(source_path):
            rel_path = md_file.relative_to(source_path).as_posix()
            text = md_file.read_text(encoding="utf-8")
            chunks = split_markdown(text, source=rel_path)

            if not chunks:
                continue

            chunks = _tag_chunks(chunks, rel_path)
            vectorstore.add_documents(chunks)
            _upsert_registry(db, rel_path, len(chunks))
            total_chunks += len(chunks)

        db.commit()
    finally:
        db.close()

    _rebuild_bm25_from_chroma(vectorstore)
    return total_chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest markdown into Chroma")
    parser.add_argument("--source", default="./data", help="Document root directory")
    args = parser.parse_args()
    count = ingest_directory(args.source)
    print(f"Ingested {count} chunks.")
