from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.models.project import ProjectCreate, ProjectUpdate
from app.services.action_engine import create_project as create_project_record, update_project
from app.services.storage_service import list_records

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/")
def list_projects():
    return list_records("projects")


@router.post("/")
def create_project(project: ProjectCreate):
    return create_project_record(project.model_dump(mode="json"))


@router.patch("/{project_id}")
def patch_project(project_id: str, updates: ProjectUpdate):
    project = update_project(project_id, updates.model_dump(mode="json", exclude_none=True))
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
