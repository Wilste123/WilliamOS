from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.services.auth_context import (
    UserContext,
    clear_refreshed_tokens,
    get_current_context,
    set_current_context,
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
        context = build_context_from_tokens(access_token, x_refresh_token.strip())
        set_current_context(context)
        return context
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


def use_user_context(user: UserContext) -> UserContext:
    """Re-bind auth in the current worker thread (sync route handlers run separately from Depends)."""
    set_current_context(user)
    return user


def wrap_endpoint_with_user_context(endpoint: Callable[..., Any]) -> Callable[..., Any]:
    """Inject CurrentUser and bind auth context in the handler's worker thread."""
    if getattr(endpoint, "__user_context_wrapped__", False):
        return endpoint

    sig = inspect.signature(endpoint)
    is_async = inspect.iscoroutinefunction(endpoint)
    has_user = "user" in sig.parameters

    if has_user:
        if is_async:

            @functools.wraps(endpoint)
            async def wrapped(*args: Any, **kwargs: Any) -> Any:
                use_user_context(kwargs["user"])
                return await endpoint(*args, **kwargs)
        else:

            @functools.wraps(endpoint)
            def wrapped(*args: Any, **kwargs: Any) -> Any:
                use_user_context(kwargs["user"])
                return endpoint(*args, **kwargs)
    else:
        user_param = inspect.Parameter(
            "user",
            inspect.Parameter.KEYWORD_ONLY,
            annotation=CurrentUser,
        )
        new_sig = sig.replace(parameters=[*sig.parameters.values(), user_param])

        if is_async:

            @functools.wraps(endpoint)
            async def wrapped(*args: Any, **kwargs: Any) -> Any:
                user = kwargs.pop("user")
                use_user_context(user)
                return await endpoint(*args, **kwargs)
        else:

            @functools.wraps(endpoint)
            def wrapped(*args: Any, **kwargs: Any) -> Any:
                user = kwargs.pop("user")
                use_user_context(user)
                return endpoint(*args, **kwargs)

        wrapped.__signature__ = new_sig  # type: ignore[attr-defined]

    wrapped.__user_context_wrapped__ = True  # type: ignore[attr-defined]
    return wrapped


def protected_router(*args: Any, **kwargs: Any) -> APIRouter:
    """APIRouter that binds user auth context inside each route handler thread."""
    router = APIRouter(*args, **kwargs)
    original_add = router.add_api_route

    def add_api_route(path: str, endpoint: Callable[..., Any], **route_kwargs: Any):
        if endpoint is not None:
            endpoint = wrap_endpoint_with_user_context(endpoint)
        return original_add(path, endpoint, **route_kwargs)

    router.add_api_route = add_api_route  # type: ignore[method-assign]
    return router
