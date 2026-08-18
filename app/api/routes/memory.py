from app.api.deps import protected_router
from app.services.memory_service import get_recent_memory_text
from app.services.storage_service import list_records

router = protected_router()


@router.get("/")
def list_memory():
    return {
        "items": list_records("memory_items"),
        "text": get_recent_memory_text(),
    }
