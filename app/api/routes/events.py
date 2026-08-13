from fastapi import APIRouter

from app.models.event import EventCreate
from app.services.action_engine import create_event
from app.services.storage_service import list_records


router = APIRouter()


@router.get("/")
def list_events():
    return list_records("events")


@router.post("/")
def add_event(event: EventCreate):
    return create_event(event.model_dump(mode="json"))
