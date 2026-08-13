from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DecisionCreate(BaseModel):
    title: str
    summary: str | None = None
    status: str = "open"
    next_action: str | None = None
    asset_id: UUID | None = None
    project_id: UUID | None = None


class Decision(DecisionCreate):
    id: UUID | None = None
    decided_at: datetime | None = None
