from pydantic import BaseModel
from uuid import UUID


class ProjectCreate(BaseModel):
    name: str
    status: str = "active"
    next_action: str | None = None
    notes: str | None = None


class Project(ProjectCreate):
    id: UUID | None = None
