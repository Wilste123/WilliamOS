from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.models.decision import DecisionCreate, DecisionUpdate
from app.services.action_engine import create_decision, update_decision
from app.services.storage_service import list_records


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/")
def list_decisions():
    return list_records("decisions")


@router.post("/")
def add_decision(decision: DecisionCreate):
    return create_decision(decision.model_dump(mode="json"))


@router.patch("/{decision_id}")
def patch_decision(decision_id: str, updates: DecisionUpdate):
    decision = update_decision(decision_id, updates.model_dump(mode="json", exclude_none=True))
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision
