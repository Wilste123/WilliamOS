from fastapi import APIRouter, UploadFile, File
from app.services.document_service import save_uploaded_file

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    saved = save_uploaded_file(file.filename, content)
    return {"saved": True, **saved}
