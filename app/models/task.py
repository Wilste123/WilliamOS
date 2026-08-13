from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None
    priority: int = 2
    asset_id: UUID | None = None
    project_id: UUID | None = None
    status: str = "open"


class Task(TaskCreate):
    id: UUID | None = None
    completed: bool = False
