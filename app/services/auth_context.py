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


def get_current_context() -> UserContext | None:
    return _current_context.get()


def set_current_context(context: UserContext | None) -> None:
    _current_context.set(context)


def require_current_context() -> UserContext:
    context = get_current_context()
    if context is None:
        raise RuntimeError("Du må være innlogget for å utføre denne handlingen.")
    return context
