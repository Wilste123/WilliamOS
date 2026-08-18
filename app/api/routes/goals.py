from fastapi import HTTPException

from app.api.deps import protected_router
from app.models.goal import GoalCreate, GoalUpdate
from app.services.action_engine import create_goal as create_goal_record, update_goal
from app.services.storage_service import list_records

router = protected_router()


@router.get("")
def list_goals():
    return list_records("goals")


@router.post("")
def create_goal(goal: GoalCreate):
    try:
        return create_goal_record(goal.model_dump(mode="json"))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/{goal_id}")
def patch_goal(goal_id: str, updates: GoalUpdate):
    goal = update_goal(goal_id, updates.model_dump(mode="json", exclude_none=True))
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal
