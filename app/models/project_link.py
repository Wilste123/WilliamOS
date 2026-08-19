from uuid import UUID

from pydantic import BaseModel, field_validator

from app.constants.project_links import PROJECT_LINK_TYPES


class ProjectLinkCreate(BaseModel):
    entity_type: str
    entity_id: UUID

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, value: str) -> str:
        if value not in PROJECT_LINK_TYPES:
            raise ValueError(f"entity_type must be one of: {', '.join(sorted(PROJECT_LINK_TYPES))}")
        return value
