from fastapi import HTTPException

from app.api.deps import protected_router
from app.models.project import ProjectCreate, ProjectUpdate
from app.models.project_link import ProjectLinkCreate
from app.services.action_engine import (
    create_project as create_project_record,
    get_project_detail,
    link_to_project,
    unlink_from_project,
    update_project,
)
from app.services.storage_service import delete_record, list_records

router = protected_router()


@router.get("")
def list_projects():
    return list_records("projects")


@router.get("/{project_id}")
def read_project(project_id: str):
    detail = get_project_detail(project_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return detail


@router.post("")
def create_project(project: ProjectCreate):
    return create_project_record(project.model_dump(mode="json"))


@router.patch("/{project_id}")
def patch_project(project_id: str, updates: ProjectUpdate):
    project = update_project(project_id, updates.model_dump(mode="json", exclude_none=True))
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/links")
def add_project_link(project_id: str, link: ProjectLinkCreate):
    try:
        return link_to_project(project_id, link.entity_type, str(link.entity_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{project_id}/links/{link_id}")
def remove_project_link(project_id: str, link_id: str):
    if not unlink_from_project(project_id, link_id):
        raise HTTPException(status_code=404, detail="Link not found")
    return {"deleted": True, "id": link_id}


@router.delete("/{project_id}")
def remove_project(project_id: str):
    if not delete_record("projects", project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True, "id": project_id}
