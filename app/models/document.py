from pydantic import BaseModel
from uuid import UUID


class Document(BaseModel):
    id: UUID | None = None
    filename: str
    storage_path: str | None = None
    asset_id: UUID | None = None
    project_id: UUID | None = None
    source_module: str | None = None
    text_content: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DocumentSearchResult(BaseModel):
    id: str
    filename: str
    source_module: str | None = None
    snippet: str
    score: float
    asset_id: str | None = None
    project_id: str | None = None
    created_at: str | None = None
