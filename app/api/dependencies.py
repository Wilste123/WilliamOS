from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException

from app.services.auth_service import get_user_from_token
from app.services.user_context import clear_current_user, set_current_user


def _parse_bearer_token(authorization: str | None) -> str:
    raw = (authorization or "").strip()
    if not raw:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    scheme, _, token = raw.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return token.strip()


async def require_authenticated_user(
    authorization: Annotated[str | None, Header()] = None,
):
    token = _parse_bearer_token(authorization)
    try:
        user = get_user_from_token(token)
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    set_current_user(user.id, user.model_dump())
    try:
        yield user
    finally:
        clear_current_user()
