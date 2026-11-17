"""多轮历史格式化测试。"""
from backend.agent.history import format_history_block, trim_history


def test_trim_history_keeps_recent_turns():
    messages = [{"role": "user", "content": f"q{i}"} for i in range(20)]
    trimmed = trim_history(messages, max_turns=2)
    assert len(trimmed) == 4


def test_format_history_block_empty():
    assert "无此前对话" in format_history_block([])


def test_format_history_block_includes_roles():
    text = format_history_block(
        [
            {"role": "user", "content": "企业版多少钱"},
            {"role": "assistant", "content": "99元每月"},
        ]
    )
    assert "用户" in text and "助手" in text
