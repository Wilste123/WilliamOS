from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.services.usage_service import get_usage_stats, record_app_open

router = APIRouter(dependencies=[Depends(get_current_user)])


class UsageStatsResponse(BaseModel):
    days_opened_this_week: int
    total_opens: int
    streak_days: int
    last_opened_at: str | None
    seven_day_goal_met: bool


@router.get("", response_model=UsageStatsResponse)
def usage_stats():
    return get_usage_stats()


@router.post("/open", response_model=UsageStatsResponse)
def log_app_open():
    return record_app_open()
