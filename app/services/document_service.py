from pathlib import Path
from uuid import uuid4

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_TEXT_BYTES = 50_000
TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".log", ".html", ".htm",
    ".xml", ".yaml", ".yml", ".py", ".js", ".ts", ".rst",
}


def extract_text_content(filename: str, content: bytes) -> str | None:
    """Extract plain-text from file bytes. Returns None for unsupported/binary files."""
    if not content:
        return None
    suffix = Path(filename).suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        try:
            text = content[:MAX_TEXT_BYTES].decode("utf-8", errors="replace")
            return text.strip() or None
        except Exception:
            return None
    try:
        text = content[:MAX_TEXT_BYTES].decode("utf-8")
        return text.strip() or None
    except (UnicodeDecodeError, ValueError):
        return None


def save_uploaded_file(filename: str, content: bytes) -> dict:
    safe_name = filename.replace("/", "_").replace("\\", "_")
    stored_name = f"{uuid4()}_{safe_name}"
    path = UPLOAD_DIR / stored_name
    path.write_bytes(content)
    text_content = extract_text_content(filename, content)
    return {"filename": filename, "storage_path": str(path), "text_content": text_content}
