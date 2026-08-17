from __future__ import annotations

from fastapi import Request

from app.services.auth_context import clear_refreshed_tokens, set_current_context
from app.services.auth_core import build_context_from_tokens


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


async def auth_context_middleware(request: Request, call_next):
    """Bind auth context for the request so sync route handlers can access it."""
    authorization = request.headers.get("authorization")
    refresh_token = request.headers.get("x-refresh-token")
    access_token = _extract_bearer_token(authorization)

    if access_token and refresh_token:
        try:
            context = build_context_from_tokens(access_token, refresh_token.strip())
            set_current_context(context)
        except RuntimeError:
            # Protected routes still return 401 via Depends(get_current_user).
            pass

    try:
        return await call_next(request)
    finally:
        set_current_context(None)
        clear_refreshed_tokens()
