from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CalendarEventCreate(BaseModel):
    title: str
    description: str | None = None
    location: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    all_day: bool = False
    visibility: str = "household"
    asset_id: UUID | None = None
    project_id: UUID | None = None
    sync_google: bool = True


class CalendarEventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    location: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    all_day: bool | None = None
    visibility: str | None = None
    asset_id: UUID | None = None
    project_id: UUID | None = None
    sync_google: bool = True


class CalendarEvent(CalendarEventCreate):
    id: UUID | None = None
    source: str = "internal"
    external_id: str | None = None
    calendar_id: str | None = "primary"
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CalendarListQuery(BaseModel):
    from_date: datetime | None = Field(default=None, alias="from")
    to_date: datetime | None = Field(default=None, alias="to")
    days: int | None = None
