"""
FILE READ/WRITE TOOL
=====================
Restricted to two allow-listed directories (uploads, deliverables).
Path traversal is blocked by resolving against the base dir and checking
containment before every read/write.
"""
from pathlib import Path
from app.config import settings

_ALLOWED_ROOTS = [Path(settings.upload_dir).resolve(), Path(settings.deliverable_dir).resolve()]


def _safe_resolve(path_str: str) -> Path:
    p = Path(path_str).resolve()
    if not any(str(p).startswith(str(root)) for root in _ALLOWED_ROOTS):
        raise PermissionError(f"BLOCKED: path '{path_str}' is outside allow-listed directories.")
    return p


def read_file_tool(path_str: str) -> str:
    p = _safe_resolve(path_str)
    if not p.exists():
        raise FileNotFoundError(str(p))
    return p.read_text(encoding="utf-8", errors="replace")


def write_file_tool(path_str: str, content: str) -> str:
    p = _safe_resolve(path_str)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return str(p)


def list_files_tool(dir_str: str) -> list[str]:
    p = _safe_resolve(dir_str)
    if not p.exists():
        return []
    return [str(f) for f in p.iterdir()]
