from __future__ import annotations

from fastapi import Request

from app.services.auth_context import clear_request_state


async def auth_context_middleware(request: Request, call_next):
    """Clear auth context after each request. Token refresh runs in get_current_user only."""
    try:
        return await call_next(request)
    finally:
        clear_request_state()
