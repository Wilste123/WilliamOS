import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.services.integration_service import (
    connect_manual_provider,
    disconnect_provider,
    finish_outlook_connect,
    list_integration_statuses,
    start_outlook_connect,
    sync_provider,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


class OutlookCompleteRequest(BaseModel):
    code: str
    state: str


@router.get("")
def list_integrations():
    return list_integration_statuses()


@router.post("/{provider}/connect")
def connect_provider(provider: str):
    try:
        if provider == "outlook":
            return start_outlook_connect()
        return connect_manual_provider(provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/outlook/complete")
def outlook_complete(body: OutlookCompleteRequest):
    try:
        return finish_outlook_connect(body.code, body.state)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{provider}/disconnect")
def disconnect_integration(provider: str):
    return disconnect_provider(provider)


@router.post("/{provider}/sync")
def sync_integration(provider: str):
    try:
        return sync_provider(provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
