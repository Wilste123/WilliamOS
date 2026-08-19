from fastapi import Form, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from app.api.deps import protected_router
from app.services.action_engine import capture_document_inbox_signal, create_document, apply_document_suggestion_action
from app.services.document_intelligence import analyze_uploaded_document
from app.services.document_storage import save_uploaded_file
from app.services.retrieval_service import search_documents
from app.services.storage_service import list_records

router = protected_router()


class DocumentSuggestionApplyRequest(BaseModel):
    suggestion_id: str
    payload: dict = {}


@router.get("")
def list_documents():
    return list_records("documents")


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
