from fastapi import APIRouter
from uuid import uuid4
from app.models.task import TaskCreate
from app.database.supabase import get_supabase

router = APIRouter()
LOCAL_TASKS = []


@router.get("/")
def list_tasks():
    supabase = get_supabase()
    if supabase is None:
        return LOCAL_TASKS
    return supabase.table("tasks").select("*").order("created_at", desc=True).execute().data


@router.post("/")
def create_task(task: TaskCreate):
    supabase = get_supabase()
    payload = task.model_dump(mode="json")
    if supabase is None:
        payload["id"] = str(uuid4())
        payload["completed"] = False
        LOCAL_TASKS.append(payload)
        return payload
    return supabase.table("tasks").insert(payload).execute().data
