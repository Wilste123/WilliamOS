from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.services.action_engine import capture_inbox_entry
from app.services.storage_service import list_records


router = APIRouter(dependencies=[Depends(get_current_user)])


class InboxRequest(BaseModel):
    text: str


@router.get("/")
def list_inbox_items():
    return list_records("inbox_items")


@router.post("/")
def capture_inbox(request: InboxRequest):
    return capture_inbox_entry(request.text)
