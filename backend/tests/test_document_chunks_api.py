"""文档分块预览 API。"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_chunks_preview_arch_overview():
    response = client.get("/api/documents/chunks", params={"path": "arch/overview.md"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["index"] == 0
    assert "preview" in data[0]


def test_chunks_rejects_path_traversal():
    response = client.get("/api/documents/chunks", params={"path": "../.env"})
    assert response.status_code == 400
