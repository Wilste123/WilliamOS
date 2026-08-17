from datetime import datetime

from pydantic import BaseModel, Field


class HealthMetricCreate(BaseModel):
    metric_type: str
    value: float
    unit: str | None = None
    source: str = "manual"
    recorded_at: datetime | None = None
    notes: str | None = None


class HealthMetricUpdate(BaseModel):
    value: float | None = None
    unit: str | None = None
    recorded_at: datetime | None = None
    notes: str | None = None
