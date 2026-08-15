from __future__ import annotations

from datetime import datetime, timezone

from app.database.supabase import get_supabase
from app.models.user import AuthenticatedUser
from app.services.user_context import DEFAULT_ASSISTANT_NAME


def _require_supabase_auth(operation: str):
    supabase = get_supabase()
    if supabase is None:
        raise RuntimeError(
            f"Supabase is not configured. Cannot perform '{operation}'. "
            "Set SUPABASE_URL and SUPABASE_KEY environment variables."
        )
    return supabase


def _get_value(obj, key: str, default=None):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _get_auth_user(auth_response):
    user = _get_value(auth_response, "user")
    if user is not None:
        return user
    session = _get_value(auth_response, "session")
    return _get_value(session, "user")


def _get_session_tokens(auth_response) -> tuple[str | None, str | None]:
    session = _get_value(auth_response, "session")
    return _get_value(session, "access_token"), _get_value(session, "refresh_token")


def _normalise_profile(user, profile_row: dict | None = None) -> dict:
    metadata = _get_value(user, "user_metadata", {}) or {}
    email = (profile_row or {}).get("email") or _get_value(user, "email")
    display_name = (
        (profile_row or {}).get("full_name")
        or metadata.get("full_name")
        or metadata.get("name")
        or (email.split("@", 1)[0] if email else "Bruker")
    )
    assistant_name = (
        (profile_row or {}).get("assistant_name")
        or metadata.get("assistant_name")
        or DEFAULT_ASSISTANT_NAME
    )
    age = (profile_row or {}).get("age")
    if age is None:
        age = metadata.get("age")
    return {
        "id": _get_value(user, "id"),
        "email": email,
        "full_name": display_name,
        "age": age,
        "assistant_name": assistant_name,
        "created_at": (profile_row or {}).get("created_at"),
        "updated_at": (profile_row or {}).get("updated_at"),
    }


def _fetch_profile_row(supabase, user_id: str) -> dict | None:
    try:
        response = (
            supabase.table("user_profiles")
            .select("*")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
    except Exception:
        return None
    return response.data


def _save_profile_row(
    supabase,
    *,
    user_id: str,
    email: str,
    full_name: str,
    age: int | None,
    assistant_name: str,
) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "email": email,
        "full_name": full_name,
        "age": age,
        "assistant_name": assistant_name,
        "updated_at": now,
    }
    existing = _fetch_profile_row(supabase, user_id)
    if existing:
        response = supabase.table("user_profiles").update(payload).eq("id", user_id).execute()
        if response.data:
            return response.data[0]
        return {**existing, **payload}
    response = supabase.table("user_profiles").insert(
        {
            "id": user_id,
            "created_at": now,
            **payload,
        }
    ).execute()
    if response.data:
        return response.data[0]
    return {"id": user_id, **payload, "created_at": now}


def _build_authenticated_user(user, profile_row: dict | None, auth_response=None) -> AuthenticatedUser:
    access_token, refresh_token = _get_session_tokens(auth_response)
    return AuthenticatedUser(
        **_normalise_profile(user, profile_row),
        access_token=access_token,
        refresh_token=refresh_token,
    )


def register_user(
    *,
    email: str,
    password: str,
    full_name: str,
    age: int | None = None,
    assistant_name: str | None = None,
) -> AuthenticatedUser:
    supabase = _require_supabase_auth("register_user")
    clean_assistant_name = (assistant_name or DEFAULT_ASSISTANT_NAME).strip() or DEFAULT_ASSISTANT_NAME
    auth_response = supabase.auth.sign_up(
        {
            "email": email.strip(),
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name.strip(),
                    "age": age,
                    "assistant_name": clean_assistant_name,
                }
            },
        }
    )
    user = _get_auth_user(auth_response)
    if user is None or not _get_value(user, "id"):
        raise RuntimeError("Registrering feilet. Fikk ikke opprettet bruker.")
    profile_row = _save_profile_row(
        supabase,
        user_id=_get_value(user, "id"),
        email=email.strip(),
        full_name=full_name.strip(),
        age=age,
        assistant_name=clean_assistant_name,
    )
    return _build_authenticated_user(user, profile_row, auth_response)


def login_user(*, email: str, password: str) -> AuthenticatedUser:
    supabase = _require_supabase_auth("login_user")
    auth_response = supabase.auth.sign_in_with_password(
        {
            "email": email.strip(),
            "password": password,
        }
    )
    user = _get_auth_user(auth_response)
    if user is None or not _get_value(user, "id"):
        raise RuntimeError("Innlogging feilet. Fikk ikke hentet bruker.")
    profile_row = _fetch_profile_row(supabase, _get_value(user, "id"))
    return _build_authenticated_user(user, profile_row, auth_response)


def get_user_from_token(access_token: str) -> AuthenticatedUser:
    supabase = _require_supabase_auth("get_user_from_token")
    user_response = supabase.auth.get_user(access_token)
    user = _get_value(user_response, "user")
    if user is None or not _get_value(user, "id"):
        raise RuntimeError("Ugyldig eller utløpt innlogging.")
    profile_row = _fetch_profile_row(supabase, _get_value(user, "id"))
    return _build_authenticated_user(user, profile_row)


def logout_user(access_token: str | None, refresh_token: str | None) -> None:
    if not access_token or not refresh_token:
        return
    supabase = _require_supabase_auth("logout_user")
    supabase.auth.set_session(access_token, refresh_token)
    supabase.auth.sign_out()
