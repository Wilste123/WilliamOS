from datetime import datetime

from fastapi import HTTPException, Query

from app.api.deps import protected_router
from app.models.calendar_event import CalendarEventCreate, CalendarEventUpdate
from app.services.calendar_service import (
    create_calendar_event,
    delete_calendar_event,
    list_calendar_events,
    sync_google_calendar,
    update_calendar_event,
)

router = protected_router()


@router.get("")
def list_events(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    days: int | None = Query(default=None, ge=1, le=90),
):
    return list_calendar_events(from_date=from_date, to_date=to_date, days=days)


@router.post("")
def add_event(body: CalendarEventCreate):
    payload = body.model_dump(mode="json")
    sync_google = payload.pop("sync_google", True)
    return create_calendar_event(payload, sync_google=sync_google)


@router.patch("/{event_id}")
def patch_event(event_id: str, body: CalendarEventUpdate):
    payload = body.model_dump(mode="json", exclude_unset=True)
    sync_google = payload.pop("sync_google", True)
    record = update_calendar_event(event_id, payload, sync_google=sync_google)
    if not record:
        raise HTTPException(status_code=404, detail="Calendar event not found")
    return record


@router.delete("/{event_id}")
def remove_event(event_id: str):
    if not delete_calendar_event(event_id):
        raise HTTPException(status_code=404, detail="Calendar event not found")
    return {"deleted": True, "id": event_id}


@router.post("/sync/google")
def sync_google():
    try:
        return sync_google_calendar()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
