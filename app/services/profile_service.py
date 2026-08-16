from __future__ import annotations

from app.services.auth_context import get_current_context, set_current_context
from app.services.storage_service import get_client

DEFAULT_ASSISTANT_NAME = "WilliamOS"


def _normalize_assistant_name(name: str | None) -> str:
    cleaned = (name or "").strip()
    return cleaned or DEFAULT_ASSISTANT_NAME


def get_assistant_name() -> str:
    """Return the current user's assistant name, falling back to the default."""
    context = get_current_context()
    if context and context.assistant_name:
        return context.assistant_name

    if context is None:
        return DEFAULT_ASSISTANT_NAME

    client = get_client()
    if client is None:
        return DEFAULT_ASSISTANT_NAME

    profile = (
        client.table("user_profiles")
        .select("assistant_name")
        .eq("id", context.user_id)
        .maybe_single()
        .execute()
    )
    assistant_name = _normalize_assistant_name(
        profile.data.get("assistant_name") if profile.data else None
    )

    updated = context.__class__(
        user_id=context.user_id,
        email=context.email,
        household_id=context.household_id,
        access_token=context.access_token,
        refresh_token=context.refresh_token,
        display_name=context.display_name,
        assistant_name=assistant_name,
    )
    set_current_context(updated)
    return assistant_name


def update_assistant_name(name: str) -> str:
    """Persist assistant name for the current user and refresh auth context."""
    context = get_current_context()
    if context is None:
        raise RuntimeError("Du må være innlogget for å endre assistentnavn.")

    assistant_name = _normalize_assistant_name(name)
    client = get_client()
    if client is None:
        raise RuntimeError("Supabase er ikke konfigurert.")

    client.table("user_profiles").update({"assistant_name": assistant_name}).eq("id", context.user_id).execute()

    updated = context.__class__(
        user_id=context.user_id,
        email=context.email,
        household_id=context.household_id,
        access_token=context.access_token,
        refresh_token=context.refresh_token,
        display_name=context.display_name,
        assistant_name=assistant_name,
    )
    set_current_context(updated)
    return assistant_name
