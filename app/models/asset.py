from pydantic import BaseModel, field_validator
from uuid import UUID

from app.constants.asset_types import ASSET_TYPES


class AssetCreate(BaseModel):
    name: str
    type: str | None = None
    description: str | None = None
    status: str = "active"
    estimated_value: float | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str | None) -> str | None:
        if value is not None and value not in ASSET_TYPES:
            allowed = ", ".join(sorted(ASSET_TYPES))
            raise ValueError(f"type must be one of: {allowed}")
        return value


class AssetUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    status: str | None = None
    estimated_value: float | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str | None) -> str | None:
        if value is not None and value not in ASSET_TYPES:
            allowed = ", ".join(sorted(ASSET_TYPES))
            raise ValueError(f"type must be one of: {allowed}")
        return value


class Asset(AssetCreate):
    id: UUID | None = None
