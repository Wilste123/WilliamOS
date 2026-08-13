from pathlib import Path
from uuid import uuid4

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def save_uploaded_file(filename: str, content: bytes) -> dict:
    safe_name = filename.replace("/", "_").replace("\\", "_")
    stored_name = f"{uuid4()}_{safe_name}"
    path = UPLOAD_DIR / stored_name
    path.write_bytes(content)
    return {"filename": filename, "storage_path": str(path)}
