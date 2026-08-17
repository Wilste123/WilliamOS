from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.services.auth_context import UserContext, set_current_context
from app.services.auth_core import build_context_from_tokens


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    x_refresh_token: Annotated[str | None, Header()] = None,
) -> Generator[UserContext, None, None]:
    """Validate Supabase tokens and set request-scoped auth context."""
    access_token = _extract_bearer_token(authorization)
    if not access_token or not x_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Send Authorization and X-Refresh-Token headers.",
        )

    try:
        context = build_context_from_tokens(access_token, x_refresh_token.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    set_current_context(context)
    try:
        yield context
    finally:
        set_current_context(None)


CurrentUser = Annotated[UserContext, Depends(get_current_user)]
