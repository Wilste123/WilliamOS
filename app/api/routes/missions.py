from pydantic import BaseModel

from app.api.deps import protected_router
from app.services.mission_service import plan_mission

router = protected_router()


class MissionPlanRequest(BaseModel):
    goal: str


@router.post("/plan")
def mission_plan(request: MissionPlanRequest):
    return plan_mission(request.goal)
