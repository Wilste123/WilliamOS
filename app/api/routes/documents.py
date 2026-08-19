import mimetypes
from urllib.parse import quote

from fastapi import Form, HTTPException, Query, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel

from app.api.deps import protected_router
from app.services.action_engine import (
    capture_document_inbox_signal,
    create_document,
    apply_document_suggestion_action,
    delete_document_record,
    reanalyze_document,
)
from app.services.document_intelligence import analyze_uploaded_document
from app.services.document_storage import download_document, save_uploaded_file
from app.services.retrieval_service import search_documents
from app.services.storage_service import get_record, list_records

router = protected_router()


class DocumentSuggestionApplyRequest(BaseModel):
    suggestion_id: str
    payload: dict = {}


def _document_file_response(document_id: str, *, inline: bool) -> Response:
    document = get_record("documents", document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    storage_path = document.get("storage_path")
    if not storage_path:
        raise HTTPException(status_code=404, detail="Document has no storage path")

    try:
        content = download_document(str(storage_path))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    filename = str(document.get("filename") or "document")
    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    disposition = "inline" if inline else "attachment"
    safe_filename = quote(filename)
    headers = {
        "Content-Disposition": f"{disposition}; filename*=UTF-8''{safe_filename}",
    }
    return Response(content=content, media_type=media_type, headers=headers)


@router.get("")
def list_documents():
    return list_records("documents")


@router.get("/search")
def search(
    q: str = Query(..., description="Search query"),
    source_module: str | None = Query(None),
    project_id: str | None = Query(None),
    asset_id: str | None = Query(None),
    top_k: int = Query(5, ge=1, le=20),
):
    results = search_documents(
        q,
        source_module=source_module,
        project_id=project_id,
        asset_id=asset_id,
        top_k=top_k,
    )
    return {"query": q, "results": results}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    asset_id: str | None = Form(None),
    project_id: str | None = Form(None),
    source_module: str | None = Form(None),
):
    content = await file.read()
    selected_source_module = source_module or "documents"
    saved = save_uploaded_file(
        file.filename,
        content,
        source_module=selected_source_module,
        content_type=file.content_type,
    )
    intelligence = analyze_uploaded_document(
        file.filename,
        saved.get("text_content"),
        asset_id=asset_id,
    )
    document = create_document(
        {
            **saved,
            "asset_id": asset_id or intelligence.get("suggested_asset_id"),
            "project_id": project_id,
            "source_module": selected_source_module,
        }
    )
    inbox_signal = capture_document_inbox_signal(document, intelligence)
    return {
        "saved": True,
        **document,
        "intelligence": intelligence,
        "inbox_signal": inbox_signal,
    }


@router.get("/{document_id}/download")
def download_document_file(document_id: str):
    return _document_file_response(document_id, inline=False)


@router.get("/{document_id}/preview")
def preview_document_file(document_id: str):
    return _document_file_response(document_id, inline=True)


@router.post("/{document_id}/analyze")
def analyze_document(document_id: str):
    try:
        return reanalyze_document(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{document_id}/apply-suggestion")
def apply_document_suggestion(document_id: str, request: DocumentSuggestionApplyRequest):
    document = next((doc for doc in list_records("documents") if doc.get("id") == document_id), None)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    suggestion_id = request.suggestion_id
    payload = request.payload or {}

    try:
        return apply_document_suggestion_action(document_id, suggestion_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{document_id}")
def remove_document(document_id: str):
    if not delete_document_record(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True, "id": document_id}
