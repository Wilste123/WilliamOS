from fastapi import APIRouter, Form, UploadFile, File

from app.services.action_engine import create_document
from app.services.document_service import save_uploaded_file
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
):
    content = await file.read()
    saved = save_uploaded_file(file.filename, content)
    document = create_document(
        {
            **saved,
            "asset_id": asset_id,
            "project_id": project_id,
        }
    )
    return {"saved": True, **document}
