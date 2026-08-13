from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class TaskCreate(BaseModel):
    title: str
    due_date: datetime | None = None
    priority: int = 2
    asset_id: UUID | None = None
    project_id: UUID | None = None


class Task(TaskCreate):
    id: UUID | None = None
    completed: bool = False
