from fastapi import HTTPException

from app.api.deps import protected_router
from app.models.event import EventCreate
from app.services.action_engine import create_event
from app.services.storage_service import delete_record, list_records

router = protected_router()


@router.get("")
def list_events():
    return list_records("events")


@router.post("")
def add_event(event: EventCreate):
    return create_event(event.model_dump(mode="json"))


@router.delete("/{event_id}")
def remove_event(event_id: str):
    if not delete_record("events", event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    return {"deleted": True, "id": event_id}
