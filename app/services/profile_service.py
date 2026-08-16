from __future__ import annotations

from app.database.supabase import response_data
from app.services.auth_context import get_current_context, set_current_context
from app.services.storage_service import get_client

DEFAULT_ASSISTANT_NAME = "WilliamOS"
MIGRATION_HINT = "Kjør migrations/2026-08-16_assistant_name.sql i Supabase SQL Editor."


def _is_missing_column_error(exc: BaseException) -> bool:
    message = str(exc)
    code = getattr(exc, "code", None)
    return code == "42703" or "assistant_name" in message and "does not exist" in message


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

    try:
        response = (
            client.table("user_profiles")
            .select("assistant_name")
            .eq("id", context.user_id)
            .limit(1)
            .execute()
        )
        rows = response_data(response, []) or []
        profile_data = rows[0] if rows else {}
        assistant_name = _normalize_assistant_name(profile_data.get("assistant_name"))
    except Exception:
        assistant_name = DEFAULT_ASSISTANT_NAME

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

    try:
        response = (
            client.table("user_profiles")
            .select("id")
            .eq("id", context.user_id)
            .limit(1)
            .execute()
        )
        if response_data(response, []):
            client.table("user_profiles").update({"assistant_name": assistant_name}).eq("id", context.user_id).execute()
        else:
            client.table("user_profiles").insert(
                {
                    "id": context.user_id,
                    "display_name": context.display_name,
                    "default_household_id": context.household_id,
                    "assistant_name": assistant_name,
                }
            ).execute()
    except Exception as exc:
        if _is_missing_column_error(exc):
            raise RuntimeError(
                f"Assistentnavn er ikke aktivert i databasen ennå. {MIGRATION_HINT}"
            ) from exc
        raise

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
