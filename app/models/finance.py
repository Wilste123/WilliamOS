from datetime import datetime

from pydantic import BaseModel, Field


class FinanceAccountCreate(BaseModel):
    name: str
    account_type: str = "asset"
    balance_nok: float = 0
    institution: str | None = None
    notes: str | None = None


class FinanceAccountUpdate(BaseModel):
    name: str | None = None
    account_type: str | None = None
    balance_nok: float | None = None
    institution: str | None = None
    notes: str | None = None


class FinanceSnapshotCreate(BaseModel):
    net_worth_nok: float
    recorded_at: datetime | None = None
