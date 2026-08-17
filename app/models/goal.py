from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "active"
    next_step: str | None = None
    target_date: datetime | None = None
    progress: int = Field(default=0, ge=0, le=100)


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    next_step: str | None = None
    target_date: datetime | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
