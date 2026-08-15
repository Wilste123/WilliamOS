from __future__ import annotations

from contextvars import ContextVar

DEFAULT_ASSISTANT_NAME = "WilliamOS"

_current_user_id: ContextVar[str | None] = ContextVar("current_user_id", default=None)
_current_user_profile: ContextVar[dict | None] = ContextVar("current_user_profile", default=None)


def set_current_user(user_id: str | None, profile: dict | None = None) -> None:
    _current_user_id.set(user_id)
    _current_user_profile.set(profile or {})


def clear_current_user() -> None:
    _current_user_id.set(None)
    _current_user_profile.set(None)


def get_current_user_id() -> str | None:
    return _current_user_id.get()


def get_current_user_profile() -> dict:
    return _current_user_profile.get() or {}


def get_current_assistant_name(default: str = DEFAULT_ASSISTANT_NAME) -> str:
    profile = get_current_user_profile()
    return (profile.get("assistant_name") or default).strip() or default
