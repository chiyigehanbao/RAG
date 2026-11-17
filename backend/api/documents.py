"""文档 registry、全量 reindex 与单文件上传 API。"""
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.models import DocumentRegistry
from backend.db.session import get_db
from backend.rag.chunker import split_markdown
from backend.rag.ingest import ingest_directory, ingest_file
from backend.rag.uploads import MAX_UPLOAD_BYTES, save_markdown_upload

DATA_ROOT = Path("./data")

router = APIRouter(prefix="/api", tags=["documents"])


class DocumentOut(BaseModel):
    """已入库文档。"""

    id: str
    path: str
    status: str
    chunk_count: int


class ReindexRequest(BaseModel):
    """reindex 请求体。"""

    source: str = "./data"


class UploadResponse(BaseModel):
    """上传入库结果。"""

    status: str
    path: str
    chunks_indexed: int


class ChunkOut(BaseModel):
    """单块预览。"""

    index: int
    section: str
    char_count: int
    preview: str


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    """已入库文档列表。"""
    docs = db.query(DocumentRegistry).order_by(DocumentRegistry.path).all()
    return [
        DocumentOut(id=d.id, path=d.path, status=d.status, chunk_count=d.chunk_count)
        for d in docs
    ]


@router.post("/documents/reindex")
def reindex(body: ReindexRequest, db: Session = Depends(get_db)):
    """触发全量 re-index（会清空 Chroma 后重建）。"""
    del db
    count = ingest_directory(body.source)
    return {"status": "ok", "chunks_indexed": count}


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传 .md 文件到 data/uploads/ 并增量入库。"""
    del db

    filename = file.filename or ""
    if ".." in filename or filename.startswith(("/", "\\")):
        raise HTTPException(status_code=400, detail="非法文件名")

    if not filename.lower().endswith(".md"):
        raise HTTPException(status_code=400, detail="仅支持 .md 文件")

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail=f"文件超过 {MAX_UPLOAD_BYTES // 1024}KB 上限")

    if not raw.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")

    try:
        dest, registry_path = save_markdown_upload(raw, filename)
        count = ingest_file(dest, registry_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="入库失败，请检查 Ollama 是否运行") from exc

    return UploadResponse(status="ok", path=registry_path, chunks_indexed=count)


@router.get("/documents/chunks", response_model=list[ChunkOut])
def list_document_chunks(path: str):
    """预览某文档的分块结果（与入库策略一致，不需命中向量库）。"""
    if ".." in path or path.startswith(("/", "\\")):
        raise HTTPException(status_code=400, detail="非法路径")

    file_path = (DATA_ROOT / path).resolve()
    if not str(file_path).startswith(str(DATA_ROOT.resolve())):
        raise HTTPException(status_code=400, detail="非法路径")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="文档不存在")

    text = file_path.read_text(encoding="utf-8")
    chunks = split_markdown(text, source=path.replace("\\", "/"))
    result: list[ChunkOut] = []
    for index, doc in enumerate(chunks):
        content = doc.page_content
        result.append(
            ChunkOut(
                index=index,
                section=str(doc.metadata.get("section", "")),
                char_count=len(content),
                preview=content[:160].replace("\n", " "),
            )
        )
    return result
