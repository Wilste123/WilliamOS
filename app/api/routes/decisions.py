from fastapi import APIRouter, HTTPException

from app.models.decision import DecisionCreate
from app.services.action_engine import create_decision, update_decision
from app.services.storage_service import list_records


router = APIRouter()


@router.get("/")
def list_decisions():
    return list_records("decisions")


@router.post("/")
def add_decision(decision: DecisionCreate):
    return create_decision(decision.model_dump(mode="json"))


@router.patch("/{decision_id}")
def patch_decision(decision_id: str, updates: dict):
    decision = update_decision(decision_id, updates)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision
