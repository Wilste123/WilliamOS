from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.services.auth_context import (
    UserContext,
    clear_refreshed_tokens,
    get_current_context,
    take_refreshed_tokens,
)
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
) -> UserContext:
    """Validate Supabase tokens for protected routes."""
    context = get_current_context()
    if context is not None:
        return context

    access_token = _extract_bearer_token(authorization)
    if not access_token or not x_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Send Authorization and X-Refresh-Token headers.",
        )

    try:
        return build_context_from_tokens(access_token, x_refresh_token.strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def attach_refreshed_token_headers(response):
    """Expose rotated Supabase tokens to the browser when a refresh occurred."""
    tokens = take_refreshed_tokens()
    if tokens:
        access_token, refresh_token = tokens
        response.headers["X-Access-Token"] = access_token
        response.headers["X-Refresh-Token"] = refresh_token
        clear_refreshed_tokens()
    return response


CurrentUser = Annotated[UserContext, Depends(get_current_user)]
