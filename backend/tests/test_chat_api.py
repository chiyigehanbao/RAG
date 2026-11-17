"""Chat API 测试。"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.db.session import init_db
from backend.main import app


@pytest.fixture
def client():
    """启动测试客户端并初始化 SQLite。"""
    init_db()
    with TestClient(app) as test_client:
        yield test_client


@patch("backend.api.chat.run_agent")
def test_post_chat_returns_answer(mock_run, client):
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
    assert body["session_id"]


@patch("backend.api.chat.run_agent")
def test_delete_session(mock_run, client):
    """DELETE /api/sessions/{id} 应删除会话及关联消息。"""
    mock_run.return_value = {
        "answer": "测试回答",
        "citations": [],
        "node_trace": [],
    }
    created = client.post("/api/chat", json={"question": "待删除会话"})
    session_id = created.json()["session_id"]

    deleted = client.delete(f"/api/sessions/{session_id}")
    assert deleted.status_code == 204

    messages = client.get(f"/api/sessions/{session_id}/messages")
    assert messages.status_code == 404
