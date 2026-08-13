from fastapi import APIRouter
from uuid import uuid4
from app.models.project import ProjectCreate
from app.database.supabase import get_supabase

router = APIRouter()
LOCAL_PROJECTS = []


@router.get("/")
def list_projects():
    supabase = get_supabase()
    if supabase is None:
        return LOCAL_PROJECTS
    return supabase.table("projects").select("*").order("created_at", desc=True).execute().data


@router.post("/")
def create_project(project: ProjectCreate):
    supabase = get_supabase()
    payload = project.model_dump(mode="json")
    if supabase is None:
        payload["id"] = str(uuid4())
        LOCAL_PROJECTS.append(payload)
        return payload
    return supabase.table("projects").insert(payload).execute().data
