from pydantic import BaseModel
from uuid import UUID


class Document(BaseModel):
    id: UUID | None = None
    filename: str
    storage_path: str | None = None
    asset_id: UUID | None = None
    project_id: UUID | None = None
