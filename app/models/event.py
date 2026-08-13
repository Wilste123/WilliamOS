from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventCreate(BaseModel):
    title: str
    event_type: str = "general"
    event_date: datetime | None = None
    notes: str | None = None
    asset_id: UUID | None = None
    project_id: UUID | None = None
    decision_id: UUID | None = None


class Event(EventCreate):
    id: UUID | None = None
    created_at: datetime | None = None
