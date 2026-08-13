from fastapi import APIRouter, HTTPException

from app.models.task import TaskCreate
from app.services.action_engine import create_task as create_task_record, update_task
from app.services.storage_service import list_records

router = APIRouter()


@router.get("/")
def list_tasks():
    return list_records("tasks")


@router.post("/")
def create_task(task: TaskCreate):
    return create_task_record(task.model_dump(mode="json"))


@router.patch("/{task_id}")
def patch_task(task_id: str, updates: dict):
    task = update_task(task_id, updates)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
