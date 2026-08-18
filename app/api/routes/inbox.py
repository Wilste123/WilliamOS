from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.api.deps import protected_router
from app.services.action_engine import apply_inbox_suggestion, capture_inbox_entry, dismiss_inbox_item
from app.services.storage_service import list_records

router = protected_router()


class InboxRequest(BaseModel):
    text: str


class ApplySuggestionRequest(BaseModel):
    suggestion_index: int = Field(ge=0)


@router.get("")
def list_inbox_items():
    return list_records("inbox_items")


@router.post("")
def capture_inbox(request: InboxRequest):
    return capture_inbox_entry(request.text)


@router.post("/{inbox_id}/apply")
def apply_suggestion(inbox_id: str, request: ApplySuggestionRequest):
    try:
        return apply_inbox_suggestion(inbox_id, request.suggestion_index)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{inbox_id}/dismiss")
def dismiss_inbox(inbox_id: str):
    try:
        return dismiss_inbox_item(inbox_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
