from app.api.deps import CurrentUser, protected_router
from app.services.action_engine import build_dashboard_summary, build_home_summary, build_priority_engine, build_timeline, build_weekly_brief
from app.services.brief_service import build_daily_brief

router = protected_router()


@router.get("/home")
def home(user: CurrentUser):
    return build_home_summary(user.display_name)


@router.get("/dashboard")
def dashboard():
    return build_dashboard_summary()


@router.get("/weekly-brief")
def weekly_brief():
    return build_weekly_brief()


@router.get("/daily-brief")
def daily_brief():
    return build_daily_brief()


@router.get("/priorities")
def priorities():
    return build_priority_engine()


@router.get("/timeline")
def timeline():
    return build_timeline()
