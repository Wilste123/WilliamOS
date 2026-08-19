from __future__ import annotations

from app.database.supabase import response_data
from app.services.auth_context import get_current_context, set_current_context
from app.services.storage_service import get_client

DEFAULT_ASSISTANT_NAME = "WilliamOS"
DEFAULT_PREFERENCES = {
    "language": "nb",
    "default_asset_type": "other",
    "inbox_automation": True,
}
MIGRATION_HINT = "Kjør migrations/2026-08-16_assistant_name.sql i Supabase SQL Editor."
PREFERENCES_MIGRATION_HINT = "Kjør migrations/2026-08-19_memory_preferences.sql i Supabase SQL Editor."


def _is_missing_column_error(exc: BaseException, column: str) -> bool:
    message = str(exc)
    code = getattr(exc, "code", None)
    return code == "42703" or column in message and "does not exist" in message


def _normalize_assistant_name(name: str | None) -> str:
    cleaned = (name or "").strip()
    return cleaned or DEFAULT_ASSISTANT_NAME


def _normalize_preferences(raw: object | None) -> dict:
    if not isinstance(raw, dict):
        return dict(DEFAULT_PREFERENCES)
    merged = dict(DEFAULT_PREFERENCES)
    merged.update({key: raw[key] for key in merged if key in raw})
    return merged


def _fetch_profile_row(user_id: str) -> dict:
    client = get_client()
    if client is None:
        return {}
    try:
        response = (
            client.table("user_profiles")
            .select("display_name, assistant_name, default_household_id, preferences")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        rows = response_data(response, []) or []
        return rows[0] if rows else {}
    except Exception as exc:
        if _is_missing_column_error(exc, "preferences"):
            response = (
                client.table("user_profiles")
                .select("display_name, assistant_name, default_household_id")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            rows = response_data(response, []) or []
            row = rows[0] if rows else {}
            row["preferences"] = dict(DEFAULT_PREFERENCES)
            return row
        if _is_missing_column_error(exc, "assistant_name"):
            return {}
        raise


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
        if _is_missing_column_error(exc, "assistant_name"):
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


def get_user_profile() -> dict:
    """Return profile fields for the current user."""
    context = get_current_context()
    if context is None:
        raise RuntimeError("Du må være innlogget.")

    row = _fetch_profile_row(context.user_id)
    return {
        "user_id": context.user_id,
        "email": context.email,
        "household_id": context.household_id,
        "display_name": row.get("display_name") or context.display_name,
        "assistant_name": _normalize_assistant_name(row.get("assistant_name") or context.assistant_name),
        "preferences": _normalize_preferences(row.get("preferences")),
    }


def update_user_profile(
    *,
    display_name: str | None = None,
    assistant_name: str | None = None,
    preferences: dict | None = None,
) -> dict:
    """Update profile fields for the current user."""
    context = get_current_context()
    if context is None:
        raise RuntimeError("Du må være innlogget for å endre profil.")

    client = get_client()
    if client is None:
        raise RuntimeError("Supabase er ikke konfigurert.")

    current = get_user_profile()
    payload: dict = {}
    if display_name is not None:
        cleaned = display_name.strip()
        if cleaned:
            payload["display_name"] = cleaned
    if assistant_name is not None:
        payload["assistant_name"] = _normalize_assistant_name(assistant_name)
    if preferences is not None:
        merged = dict(current["preferences"])
        merged.update(preferences)
        payload["preferences"] = merged

    if not payload:
        return current

    try:
        response = client.table("user_profiles").select("id").eq("id", context.user_id).limit(1).execute()
        if response_data(response, []):
            client.table("user_profiles").update(payload).eq("id", context.user_id).execute()
        else:
            client.table("user_profiles").insert(
                {
                    "id": context.user_id,
                    "display_name": payload.get("display_name", context.display_name),
                    "default_household_id": context.household_id,
                    "assistant_name": payload.get("assistant_name", DEFAULT_ASSISTANT_NAME),
                    "preferences": payload.get("preferences", dict(DEFAULT_PREFERENCES)),
                }
            ).execute()
    except Exception as exc:
        if _is_missing_column_error(exc, "preferences"):
            raise RuntimeError(
                f"Preferanser er ikke aktivert i databasen ennå. {PREFERENCES_MIGRATION_HINT}"
            ) from exc
        if _is_missing_column_error(exc, "assistant_name"):
            raise RuntimeError(f"Assistentnavn er ikke aktivert i databasen ennå. {MIGRATION_HINT}") from exc
        raise

    updated_profile = get_user_profile()
    updated_context = context.__class__(
        user_id=context.user_id,
        email=context.email,
        household_id=context.household_id,
        access_token=context.access_token,
        refresh_token=context.refresh_token,
        display_name=updated_profile.get("display_name"),
        assistant_name=updated_profile.get("assistant_name"),
    )
    set_current_context(updated_context)
    return updated_profile
