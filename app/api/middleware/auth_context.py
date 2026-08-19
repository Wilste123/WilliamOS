from __future__ import annotations

from fastapi import Request

from app.services.auth_context import clear_request_state
from starlette.responses import StreamingResponse


async def auth_context_middleware(request: Request, call_next):
    """Clear auth context after each request. Defer clear until SSE streams finish."""
    try:
        response = await call_next(request)
    except Exception:
        clear_request_state()
        raise

    if isinstance(response, StreamingResponse):
        original_iterator = response.body_iterator

        async def stream_with_cleanup():
            try:
                async for chunk in original_iterator:
                    yield chunk
            finally:
                clear_request_state()

        response.body_iterator = stream_with_cleanup()
        return response

    clear_request_state()
    return response
