"""Authentication service for WilliamOS.

Wraps Supabase Auth for sign-up / sign-in / sign-out and manages the
``user_profiles`` table that stores per-user profile data (name, age,
custom assistant name, etc.).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.database.supabase import get_supabase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_supabase(operation: str):
    sb = get_supabase()
    if sb is None:
        raise RuntimeError(
            f"Supabase is not configured. Cannot perform '{operation}'. "
            "Set SUPABASE_URL and SUPABASE_KEY environment variables."
        )
    return sb


# ---------------------------------------------------------------------------
# Auth operations
# ---------------------------------------------------------------------------


def register(
    email: str,
    password: str,
    *,
    name: str = "",
    age: int | None = None,
    assistant_name: str = "Jarvis",
) -> dict:
    """Register a new user and create their profile.

    Returns a dict with keys ``user`` (Supabase User object) and
    ``session`` (Supabase Session object), or raises on failure.
    """
    sb = _require_supabase("register")
    response = sb.auth.sign_up({"email": email, "password": password})
    if response.user is None:
        raise RuntimeError("Registration failed: no user returned from Supabase.")

    user_id = response.user.id
    _upsert_profile(sb, user_id, name=name, age=age, assistant_name=assistant_name)

    return {"user": response.user, "session": response.session}


def login(email: str, password: str) -> dict:
    """Sign in an existing user.

    Returns a dict with keys ``user`` and ``session``, or raises on failure.
    """
    sb = _require_supabase("login")
    response = sb.auth.sign_in_with_password({"email": email, "password": password})
    if response.user is None:
        raise RuntimeError("Login failed: invalid email or password.")
    return {"user": response.user, "session": response.session}


def logout() -> None:
    """Sign out the currently authenticated user."""
    sb = _require_supabase("logout")
    sb.auth.sign_out()


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------


def get_user_profile(user_id: str) -> dict | None:
    """Return the profile row for *user_id*, or None if not found."""
    sb = _require_supabase("get_user_profile")
    response = (
        sb.table("user_profiles")
        .select("*")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    return response.data


def update_user_profile(user_id: str, updates: dict) -> dict | None:
    """Update profile fields for *user_id*.

    Returns the updated row, or None if no matching row existed.
    """
    sb = _require_supabase("update_user_profile")
    patch = {**updates, "updated_at": datetime.now(timezone.utc).isoformat()}
    response = (
        sb.table("user_profiles").update(patch).eq("user_id", user_id).execute()
    )
    if response.data:
        return response.data[0]
    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _upsert_profile(
    sb,
    user_id: str,
    *,
    name: str,
    age: int | None,
    assistant_name: str,
) -> None:
    """Insert or update the user_profiles row for *user_id* atomically."""
    now = datetime.now(timezone.utc).isoformat()
    profile = {
        "user_id": user_id,
        "name": name,
        "age": age,
        "assistant_name": assistant_name or "Jarvis",
        "created_at": now,
        "updated_at": now,
    }
    sb.table("user_profiles").upsert(profile, on_conflict="user_id").execute()
