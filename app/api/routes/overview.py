from fastapi import APIRouter

from app.services.action_engine import build_dashboard_summary, build_timeline


router = APIRouter()


@router.get("/dashboard")
def dashboard():
    return build_dashboard_summary()


@router.get("/timeline")
def timeline():
    return build_timeline()
