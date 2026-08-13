from fastapi import APIRouter, Form, Query, UploadFile, File

from app.services.action_engine import create_document
from app.services.document_service import save_uploaded_file
from app.services.retrieval_service import search_documents
from app.services.storage_service import list_records

router = APIRouter()


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
    saved = save_uploaded_file(file.filename, content)
    document = create_document(
        {
            **saved,
            "asset_id": asset_id,
            "project_id": project_id,
            "source_module": source_module or "documents",
        }
    )
    return {"saved": True, **document}


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
