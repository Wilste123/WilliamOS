"""Keyword-based document retrieval for chat context injection."""

from __future__ import annotations

import re

from app.services.storage_service import list_records

MAX_SNIPPET_CHARS = 400
MAX_RESULTS = 5
MAX_CONTENT_CHARS = 4000


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _score(query_tokens: set[str], doc: dict) -> float:
    """Return a simple overlap score between query tokens and document text/metadata."""
    haystack = " ".join(
        filter(
            None,
            [
                doc.get("text_content") or "",
                doc.get("filename") or "",
                doc.get("source_module") or "",
            ],
        )
    ).lower()
    doc_tokens = _tokenize(haystack)
    if not doc_tokens:
        return 0.0
    overlap = query_tokens & doc_tokens
    return len(overlap) / max(len(query_tokens), 1)


def _extract_snippet(query_tokens: set[str], text: str) -> str:
    """Return the most relevant ~400-char window from text."""
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?\n])\s+", text)
    best_sentence = ""
    best_count = -1
    for sentence in sentences:
        count = len(query_tokens & _tokenize(sentence))
        if count > best_count:
            best_count = count
            best_sentence = sentence
    if best_sentence:
        return best_sentence[:MAX_SNIPPET_CHARS]
    return text[:MAX_SNIPPET_CHARS]


def search_documents(
    query: str,
    *,
    source_module: str | None = None,
    project_id: str | None = None,
    asset_id: str | None = None,
    top_k: int = MAX_RESULTS,
) -> list[dict]:
    """
    Search stored documents by keyword overlap.

    Returns a list of dicts with keys:
        id, filename, source_module, snippet, score, asset_id, project_id, created_at
    """
    if not query.strip():
        return []

    query_tokens = _tokenize(query)
    documents = list_records("documents")

    results = []
    for doc in documents:
        if source_module and doc.get("source_module") != source_module:
            continue
        if project_id and doc.get("project_id") != project_id:
            continue
        if asset_id and doc.get("asset_id") != asset_id:
            continue

        score = _score(query_tokens, doc)
        if score <= 0:
            continue

        snippet = _extract_snippet(query_tokens, doc.get("text_content") or "")
        results.append(
            {
                "id": doc.get("id", ""),
                "filename": doc.get("filename", ""),
                "source_module": doc.get("source_module"),
                "snippet": snippet,
                "score": score,
                "asset_id": doc.get("asset_id"),
                "project_id": doc.get("project_id"),
                "created_at": doc.get("created_at"),
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


def build_document_context(query: str, *, top_k: int = MAX_RESULTS) -> tuple[str, list[dict]]:
    """
    Build a context string and source list for injection into a chat prompt.

    Returns:
        (context_text, sources)  where sources is the list of matching result dicts.
    """
    hits = search_documents(query, top_k=top_k)
    if not hits:
        return "", []

    # Re-fetch full text_content for the matched documents so the model can read
    # and analyze them – not just see a short metadata snippet.
    documents_by_id = {
        doc.get("id"): doc
        for doc in list_records("documents")
        if doc.get("id")
    }

    lines = [
        "The following documents from your workspace are relevant to the user's question.",
        "Read their full content carefully and use it to answer.\n",
    ]
    for i, hit in enumerate(hits, 1):
        full_doc = documents_by_id.get(hit["id"], {})
        text_content = (full_doc.get("text_content") or hit.get("snippet") or "").strip()
        if len(text_content) > MAX_CONTENT_CHARS:
            text_content = text_content[:MAX_CONTENT_CHARS] + "\n[... content truncated ...]"

        lines.append(
            f"--- Document {i}: {hit['filename']} "
            f"(module: {hit.get('source_module') or 'unknown'}) ---"
        )
        if text_content:
            lines.append(text_content)
        else:
            lines.append("(No text content available for this document.)")
        lines.append("")

    return "\n".join(lines), hits
