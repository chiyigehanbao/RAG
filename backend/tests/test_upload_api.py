"""文档上传 API 测试。"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.db.session import init_db
from backend.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _init_db():
    init_db()
    yield


@patch("backend.api.documents.ingest_file")
@patch("backend.api.documents.save_markdown_upload")
def test_upload_markdown_ok(mock_save, mock_ingest, tmp_path):
    """合法 .md 应返回 path 与 chunk 数。"""
    dest = tmp_path / "uploads" / "ab_test.md"
    dest.parent.mkdir(parents=True)
    dest.write_text("## 标题\n\n内容", encoding="utf-8")
    mock_save.return_value = (dest, "uploads/ab_test.md")
    mock_ingest.return_value = 2

    response = client.post(
        "/api/documents/upload",
        files={"file": ("notes.md", b"## T\n\nhello", "text/markdown")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["path"] == "uploads/ab_test.md"
    assert body["chunks_indexed"] == 2


def test_upload_rejects_non_md():
    """非 .md 扩展名应 400。"""
    response = client.post(
        "/api/documents/upload",
        files={"file": ("bad.txt", b"text", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_rejects_path_traversal():
    """路径穿越文件名应 400。"""
    response = client.post(
        "/api/documents/upload",
        files={"file": ("../evil.md", b"## x", "text/markdown")},
    )
    assert response.status_code == 400


@patch("backend.api.documents.ingest_file", side_effect=RuntimeError("ollama down"))
@patch("backend.api.documents.save_markdown_upload")
def test_upload_ingest_failure(mock_save, _mock_ingest, tmp_path):
    """入库异常应 500。"""
    dest = tmp_path / "x.md"
    dest.write_text("## a", encoding="utf-8")
    mock_save.return_value = (dest, "uploads/x.md")

    response = client.post(
        "/api/documents/upload",
        files={"file": ("ok.md", b"## T\n\nb", "text/markdown")},
    )
    assert response.status_code == 500
