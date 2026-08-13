from pydantic import BaseModel
from uuid import UUID


class AssetCreate(BaseModel):
    name: str
    type: str | None = None
    description: str | None = None
    status: str = "active"
    estimated_value: float | None = None


class Asset(AssetCreate):
    id: UUID | None = None
