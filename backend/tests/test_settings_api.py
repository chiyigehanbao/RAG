"""助手设定 API 测试。"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.runtime import _SETTINGS_FILE, reset_runtime_cache

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_runtime_settings():
    reset_runtime_cache()
    if _SETTINGS_FILE.exists():
        _SETTINGS_FILE.unlink()
    yield
    reset_runtime_cache()
    if _SETTINGS_FILE.exists():
        _SETTINGS_FILE.unlink()


def test_get_and_update_settings():
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "RAG 架构助手"
    assert data["retrieval_scope"] == "auto"

    updated = client.put("/api/settings", json={"product_name": "智汇云", "retrieve_top_k": 8})
    assert updated.status_code == 200
    assert updated.json()["product_name"] == "智汇云"
    assert updated.json()["retrieve_top_k"] == 8

    assert _SETTINGS_FILE.exists()
    saved = json.loads(Path(_SETTINGS_FILE).read_text(encoding="utf-8"))
    assert saved["product_name"] == "智汇云"
