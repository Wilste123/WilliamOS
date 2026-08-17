from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.services.action_engine import build_dashboard_summary, build_timeline, build_weekly_brief


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/dashboard")
def dashboard():
    return build_dashboard_summary()


@router.get("/weekly-brief")
def weekly_brief():
    return build_weekly_brief()


@router.get("/timeline")
def timeline():
    return build_timeline()
