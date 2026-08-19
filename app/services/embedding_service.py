"""OpenAI embeddings for semantic document search."""

from __future__ import annotations

import logging
import math
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
MAX_EMBED_CHARS = 12_000

try:
    from openai import OpenAI

    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
except Exception:  # noqa: BLE001
    _client = None


def embeddings_enabled() -> bool:
    return _client is not None


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=False))


def embed_text(text: str) -> list[float] | None:
    if _client is None:
        return None
    cleaned = (text or "").strip()
    if not cleaned:
        return None
    if len(cleaned) > MAX_EMBED_CHARS:
        cleaned = cleaned[:MAX_EMBED_CHARS]
    try:
        response = _client.embeddings.create(model=EMBEDDING_MODEL, input=cleaned)
        vector = response.data[0].embedding
        return _normalize(vector)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Embedding failed: %s", exc)
        return None


def index_document_embedding(document_id: str, *, text: str | None = None) -> bool:
    from app.services.storage_service import get_record, update_record

    document = get_record("documents", document_id)
    if not document:
        return False

    body = (text if text is not None else document.get("text_content") or "").strip()
    if not body and document.get("storage_path"):
        from app.services.document_storage import read_document_text

        body = (read_document_text(str(document["storage_path"]), document.get("filename")) or "").strip()

    vector = embed_text(body)
    if vector is None:
        return False

    update_record(
        "documents",
        document_id,
        {
            "embedding": vector,
            "embedding_model": EMBEDDING_MODEL,
            "embedded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return True


def reindex_all_documents() -> dict:
    from app.services.storage_service import list_records

    indexed = 0
    skipped = 0
    for document in list_records("documents"):
        doc_id = str(document.get("id") or "")
        if not doc_id:
            skipped += 1
            continue
        if index_document_embedding(doc_id):
            indexed += 1
        else:
            skipped += 1
    return {"indexed": indexed, "skipped": skipped, "total": indexed + skipped}
