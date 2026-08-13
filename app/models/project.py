from pydantic import BaseModel
from uuid import UUID


class ProjectCreate(BaseModel):
    name: str
    status: str = "active"
    next_action: str | None = None
    notes: str | None = None
    asset_id: UUID | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    next_action: str | None = None
    notes: str | None = None
    asset_id: UUID | None = None


class Project(ProjectCreate):
    id: UUID | None = None
