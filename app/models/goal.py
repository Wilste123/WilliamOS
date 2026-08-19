from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.constants.goal_modules import GOAL_MODULES


class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "active"
    next_step: str | None = None
    target_date: datetime | None = None
    progress: int = Field(default=0, ge=0, le=100)
    module: str | None = None
    linked_id: UUID | None = None

    @field_validator("module")
    @classmethod
    def validate_module(cls, value: str | None) -> str | None:
        if value is not None and value not in GOAL_MODULES:
            raise ValueError(f"module must be one of: {', '.join(sorted(GOAL_MODULES))}")
        return value


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    next_step: str | None = None
    target_date: datetime | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    module: str | None = None
    linked_id: UUID | None = None

    @field_validator("module")
    @classmethod
    def validate_module(cls, value: str | None) -> str | None:
        if value is not None and value not in GOAL_MODULES:
            raise ValueError(f"module must be one of: {', '.join(sorted(GOAL_MODULES))}")
        return value
