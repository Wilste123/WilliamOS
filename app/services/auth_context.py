from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class UserContext:
    user_id: str
    email: str
    household_id: str
    access_token: str
    refresh_token: str
    display_name: str | None = None
    assistant_name: str | None = None


_current_context: ContextVar[UserContext | None] = ContextVar("current_context", default=None)
_refreshed_tokens: ContextVar[tuple[str, str] | None] = ContextVar("refreshed_tokens", default=None)


def get_current_context() -> UserContext | None:
    return _current_context.get()


def set_current_context(context: UserContext | None) -> None:
    _current_context.set(context)


def mark_refreshed_tokens(access_token: str, refresh_token: str) -> None:
    _refreshed_tokens.set((access_token, refresh_token))


def take_refreshed_tokens() -> tuple[str, str] | None:
    return _refreshed_tokens.get()


def clear_refreshed_tokens() -> None:
    _refreshed_tokens.set(None)


def require_current_context() -> UserContext:
    context = get_current_context()
    if context is None:
        raise RuntimeError("Du må være innlogget for å utføre denne handlingen.")
    return context
