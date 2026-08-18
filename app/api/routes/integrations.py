from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentUser, use_user_context
from app.services.integration_service import (
    connect_manual_provider,
    disconnect_provider,
    finish_google_connect,
    list_integration_statuses,
    start_google_connect,
    sync_provider,
)

router = APIRouter()


class GoogleCompleteRequest(BaseModel):
    code: str
    state: str


@router.get("")
def list_integrations(user: CurrentUser):
    use_user_context(user)
    return list_integration_statuses()


@router.post("/{provider}/connect")
def connect_provider(provider: str, user: CurrentUser):
    use_user_context(user)
    try:
        if provider == "google":
            return start_google_connect()
        return connect_manual_provider(provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/google/complete")
def google_complete(body: GoogleCompleteRequest, user: CurrentUser):
    use_user_context(user)
    try:
        return finish_google_connect(body.code, body.state)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{provider}/disconnect")
def disconnect_integration(provider: str, user: CurrentUser):
    use_user_context(user)
    return disconnect_provider(provider)


@router.post("/{provider}/sync")
def sync_integration(provider: str, user: CurrentUser):
    use_user_context(user)
    try:
        return sync_provider(provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
