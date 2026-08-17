from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile, File
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.services.action_engine import create_document, create_task, update_asset
from app.services.document_intelligence import analyze_uploaded_document
from app.services.document_storage import save_uploaded_file
from app.services.retrieval_service import search_documents
from app.services.storage_service import list_records, update_record

router = APIRouter(dependencies=[Depends(get_current_user)])


class DocumentSuggestionApplyRequest(BaseModel):
    suggestion_id: str
    payload: dict = {}


@router.get("/")
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
    return {
        "saved": True,
        **document,
        "intelligence": intelligence,
    }


@router.post("/{document_id}/apply-suggestion")
def apply_document_suggestion(document_id: str, request: DocumentSuggestionApplyRequest):
    document = next((doc for doc in list_records("documents") if doc.get("id") == document_id), None)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    suggestion_id = request.suggestion_id
    payload = request.payload or {}

    if suggestion_id == "link_asset":
        asset_id = payload.get("asset_id")
        if not asset_id:
            raise HTTPException(status_code=400, detail="asset_id required")
        updated = update_record("documents", document_id, {"asset_id": asset_id})
        return {"applied": True, "document": updated, "action": "link_asset"}

    if suggestion_id == "update_insurance":
        asset_id = payload.get("asset_id")
        if not asset_id:
            raise HTTPException(status_code=400, detail="asset_id required")
        note = f"Forsikring oppdatert via dokument: {document.get('filename')}"
        asset = update_asset(asset_id, {"description": note})
        update_record("documents", document_id, {"asset_id": asset_id})
        return {"applied": True, "asset": asset, "action": "update_insurance"}

    if suggestion_id == "create_service_task":
        task = create_task(
            {
                "title": payload.get("title") or f"Service: {document.get('filename')}",
                "asset_id": payload.get("asset_id") or document.get("asset_id"),
                "priority": payload.get("priority", 2),
                "status": "open",
            }
        )
        return {"applied": True, "task": task, "action": "create_service_task"}

    raise HTTPException(status_code=400, detail="Unknown suggestion")


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
