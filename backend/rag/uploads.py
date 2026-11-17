"""上传文件：校验、文件名消毒与落盘。"""
import re
import uuid
from pathlib import Path

MAX_UPLOAD_BYTES = 512 * 1024
UPLOAD_SUBDIR = "uploads"


def sanitize_filename(name: str) -> str:
    """
    去除路径成分，仅保留安全字符。

    Args:
        name: 用户原始文件名

    Returns:
        安全文件名（含 .md 后缀时保留）
    """
    base = Path(name).name
    if not base or base in {".", ".."}:
        base = "document.md"

    stem = Path(base).stem[:80] or "document"
    suffix = Path(base).suffix.lower()
    if suffix != ".md":
        suffix = ".md"

    safe_stem = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]", "_", stem).strip("_")
    if not safe_stem:
        safe_stem = "document"
    return f"{safe_stem}{suffix}"


def save_markdown_upload(content: bytes, original_filename: str, data_root: Path | None = None) -> tuple[Path, str]:
    """
    将上传内容写入 data/uploads/。

    Args:
        content: 文件二进制内容
        original_filename: 原始文件名
        data_root: 数据根目录，默认 ./data

    Returns:
        (绝对路径, registry 相对路径如 uploads/xxx.md)
    """
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError(f"文件超过 {MAX_UPLOAD_BYTES // 1024}KB 上限")

    root = data_root or Path("./data")
    upload_dir = root / UPLOAD_SUBDIR
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_filename(original_filename)
    stored_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    dest = upload_dir / stored_name
    dest.write_bytes(content)

    registry_path = f"{UPLOAD_SUBDIR}/{stored_name}".replace("\\", "/")
    return dest, registry_path
