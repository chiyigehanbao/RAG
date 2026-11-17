from backend.agent.text_format import plain_answer_text


def test_plain_answer_strips_bold_markers():
    raw = "1. **前端请求**：说明\n2. **编排**：分类 -> 检索"
    assert "**" not in plain_answer_text(raw)
    assert "前端请求" in plain_answer_text(raw)
