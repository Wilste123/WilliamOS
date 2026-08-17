from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.services.memory_service import get_recent_memory_text
from app.services.storage_service import list_records

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/")
def list_memory():
    return {
        "items": list_records("memory_items"),
        "text": get_recent_memory_text(),
    }
