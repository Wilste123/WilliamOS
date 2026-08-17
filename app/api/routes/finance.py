from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.models.finance import FinanceAccountCreate, FinanceAccountUpdate, FinanceSnapshotCreate
from app.services.finance_service import (
    compute_net_worth,
    create_finance_account,
    create_finance_snapshot,
    update_finance_account,
)
from app.services.storage_service import list_records

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/summary")
def finance_summary():
    return compute_net_worth()


@router.get("/accounts")
def list_accounts():
    return list_records("finance_accounts")


@router.post("/accounts")
def create_account(account: FinanceAccountCreate):
    try:
        return create_finance_account(account.model_dump(mode="json"))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/accounts/{account_id}")
def patch_account(account_id: str, updates: FinanceAccountUpdate):
    account = update_finance_account(account_id, updates.model_dump(mode="json", exclude_none=True))
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("/snapshots")
def list_snapshots():
    return list_records("finance_snapshots")


@router.post("/snapshots")
def create_snapshot(body: FinanceSnapshotCreate):
    try:
        return create_finance_snapshot(body.net_worth_nok, body.recorded_at)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
