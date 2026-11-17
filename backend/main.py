"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.chat import router as chat_router
from backend.api.debug import router as debug_router
from backend.api.documents import router as documents_router
from backend.api.settings import router as settings_router
from backend.config import get_settings
from backend.db.session import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化 SQLite 表。"""
    init_db()
    yield


app = FastAPI(title="RAG 架构助手", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(debug_router)
app.include_router(documents_router)
app.include_router(settings_router)
