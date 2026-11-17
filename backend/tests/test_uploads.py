"""上传工具函数测试。"""
import pytest

from backend.rag.uploads import sanitize_filename, save_markdown_upload


def test_sanitize_strips_path():
    """应去掉路径只保留文件名。"""
    assert sanitize_filename("../../etc/pass.md").endswith(".md")
    assert ".." not in sanitize_filename("../../evil.md")


def test_save_upload_writes_file(tmp_path):
    """应写入 data/uploads 并返回 registry 路径。"""
    data_root = tmp_path / "data"
    dest, rel = save_markdown_upload(b"## Hi\n\nbody", "我的文档.md", data_root=data_root)
    assert dest.is_file()
    assert rel.startswith("uploads/")
    assert rel.endswith(".md")


def test_save_upload_size_limit(tmp_path):
    """超大文件应拒绝。"""
    from backend.rag.uploads import MAX_UPLOAD_BYTES

    huge = b"x" * (MAX_UPLOAD_BYTES + 1)
    with pytest.raises(ValueError, match="上限"):
        save_markdown_upload(huge, "big.md", data_root=tmp_path / "data")
