import mimetypes
import os
from pathlib import Path
from uuid import uuid4

from app.services.auth_context import get_current_context
from app.services.storage_service import get_client

MAX_TEXT_BYTES = 50_000
TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".log", ".html", ".htm",
    ".xml", ".yaml", ".yml", ".py", ".js", ".ts", ".rst",
}

DEFAULT_DOCUMENTS_BUCKET = "documents"


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


def _require_storage(operation: str):
    client = get_client()
    if client is None:
        raise RuntimeError(
            f"Supabase is not configured. Cannot perform '{operation}' for documents. "
            "Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
        )
    bucket = get_documents_bucket()
    return client.storage.from_(bucket)


def get_documents_bucket() -> str:
    raw_bucket = os.getenv("DOCUMENTS_BUCKET")
    if raw_bucket is None:
        return DEFAULT_DOCUMENTS_BUCKET
    bucket = raw_bucket.strip()
    if not bucket or "your_" in bucket:
        raise RuntimeError(
            "DOCUMENTS_BUCKET is misconfigured. Set DOCUMENTS_BUCKET to a valid Supabase Storage bucket name."
        )
    return bucket


def _sanitize_path_component(value: str | None) -> str:
    cleaned = (value or "documents").strip().strip("/")
    if not cleaned:
        return "documents"
    return "".join(char if char.isalnum() or char in {"-", "_", "/"} else "_" for char in cleaned)


def _build_storage_prefix(*, visibility: str, source_module: str | None) -> str:
    context = get_current_context()
    module = _sanitize_path_component(source_module or "documents")
    if visibility == "private":
        if context is None:
            return f"private/unknown/{module}"
        return f"private/{context.user_id}/{module}"
    if context is None:
        return f"household/unknown/{module}"
    return f"household/{context.household_id}/{module}"


def upload_document(
    filename: str,
    content: bytes,
    *,
    source_module: str | None = None,
    content_type: str | None = None,
    visibility: str = "household",
) -> dict:
    storage = _require_storage("upload_document")
    safe_name = Path(filename).name.replace("/", "_").replace("\\", "_") or "document"
    prefix = _build_storage_prefix(visibility=visibility, source_module=source_module)
    storage_path = f"{prefix}/{uuid4()}_{safe_name}"
    file_options = {
        "content-type": content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream",
        "upsert": "false",
    }
    storage.upload(path=storage_path, file=content, file_options=file_options)
    text_content = extract_text_content(filename, content)
    return {"filename": filename, "storage_path": storage_path, "text_content": text_content}


def download_document(storage_path: str) -> bytes:
    storage = _require_storage("download_document")
    return storage.download(storage_path)


def read_document_text(storage_path: str, filename: str | None = None) -> str | None:
    content = download_document(storage_path)
    return extract_text_content(filename or storage_path, content)


def list_document_objects(path: str | None = None) -> list[dict]:
    storage = _require_storage("list_document_objects")
    return storage.list(path=path or "")


def delete_document(storage_path: str) -> None:
    storage = _require_storage("delete_document")
    storage.remove([storage_path])


def save_uploaded_file(
    filename: str,
    content: bytes,
    *,
    source_module: str | None = None,
    content_type: str | None = None,
    visibility: str = "household",
) -> dict:
    return upload_document(
        filename,
        content,
        source_module=source_module,
        content_type=content_type,
        visibility=visibility,
    )
