from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.services.integration_service import (
    connect_manual_provider,
    disconnect_provider,
    finish_google_connect,
    list_integration_statuses,
    start_google_connect,
    sync_provider,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


class GoogleCompleteRequest(BaseModel):
    code: str
    state: str


@router.get("")
def list_integrations():
    return list_integration_statuses()


@router.post("/{provider}/connect")
def connect_provider(provider: str):
    try:
        if provider == "google":
            return start_google_connect()
        return connect_manual_provider(provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/google/complete")
def google_complete(body: GoogleCompleteRequest):
    try:
        return finish_google_connect(body.code, body.state)
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
