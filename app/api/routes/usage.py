from pydantic import BaseModel

from app.api.deps import protected_router
from app.services.usage_service import get_usage_stats, record_app_open

router = protected_router()


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
