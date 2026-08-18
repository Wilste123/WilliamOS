from __future__ import annotations

import threading
import time

from app.database.supabase import get_authenticated_client, get_supabase_anon, response_data
from app.services.auth_context import UserContext

_refresh_lock = threading.Lock()
_rotation_cache: dict[str, tuple[str, str, float]] = {}
_ROTATION_CACHE_TTL_SEC = 30


def _cache_token_rotation(old_refresh: str, access_token: str, new_refresh: str) -> None:
    with _refresh_lock:
        _rotation_cache[old_refresh] = (
            access_token,
            new_refresh,
            time.monotonic() + _ROTATION_CACHE_TTL_SEC,
        )


def _lookup_token_rotation(old_refresh: str) -> tuple[str, str] | None:
    with _refresh_lock:
        entry = _rotation_cache.get(old_refresh)
        if not entry:
            return None
        access_token, new_refresh, expires_at = entry
        if time.monotonic() > expires_at:
            _rotation_cache.pop(old_refresh, None)
            return None
        return access_token, new_refresh


def _raise_auth_error(exc: Exception) -> None:
    """Convert Supabase auth exceptions into user-facing RuntimeErrors."""
    message = str(getattr(exc, "message", None) or exc)
    code = str(getattr(exc, "code", "") or "")

    if code == "invalid_credentials" or "Invalid login credentials" in message:
        raise RuntimeError("Ugyldig e-post eller passord.") from exc
    if code == "email_not_confirmed" or "Email not confirmed" in message:
        raise RuntimeError("Bekreft e-posten din før du logger inn.") from exc
    if "already registered" in message.lower() or code == "user_already_exists":
        raise RuntimeError("E-postadressen er allerede registrert.") from exc
    if "already used" in message.lower():
        raise RuntimeError("Sesjonen er utløpt. Logg ut og logg inn på nytt.") from exc
    if "403" in message or "Forbidden" in message:
        raise RuntimeError(
            "Supabase autentisering feilet. Sjekk SUPABASE_URL og SUPABASE_ANON_KEY i .env."
        ) from exc
    if "expired" in message.lower() or "invalid jwt" in message.lower():
        raise RuntimeError("Sesjonen er utløpt. Logg inn på nytt.") from exc
    raise RuntimeError(f"Autentisering feilet: {message}") from exc


def _build_context(
    session,
    user,
    household_id: str,
    display_name: str | None = None,
    assistant_name: str | None = None,
) -> UserContext:
    return UserContext(
        user_id=user.id,
        email=user.email or "",
        household_id=household_id,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        display_name=display_name,
        assistant_name=assistant_name,
    )


def _extract_display_name(user) -> str | None:
    metadata = getattr(user, "user_metadata", None) or {}
    if isinstance(metadata, dict):
        name = metadata.get("display_name") or metadata.get("full_name") or metadata.get("name")
        if name:
            return str(name).strip()
    return None


def _first_row(response, default=None):
    rows = response_data(response, []) or []
    if not rows:
        return default
    return rows[0]


def _load_profile(client, user_id: str) -> dict:
    response = (
        client.table("user_profiles")
        .select("display_name, default_household_id")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return _first_row(response, {}) or {}


def _find_household_id(client, user_id: str) -> str | None:
    profile = _load_profile(client, user_id)
    if profile.get("default_household_id"):
        return profile["default_household_id"]

    membership = (
        client.table("household_members")
        .select("household_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    row = _first_row(membership)
    if row:
        return row["household_id"]
    return None


def ensure_user_provisioned(client, user, display_name: str | None = None) -> str:
    """Create household/profile/membership on first login when signup deferred setup."""
    existing = _find_household_id(client, user.id)
    if existing:
        profile = _load_profile(client, user.id)
        if not profile.get("default_household_id"):
            client.table("user_profiles").update({"default_household_id": existing}).eq("id", user.id).execute()
        return existing

    label = display_name or _extract_display_name(user) or (user.email.split("@")[0] if user.email else "Min")
    household = (
        client.table("households")
        .insert({"name": f"{label}s husholdning", "created_by": user.id})
        .execute()
    )
    household_row = _first_row(household)
    if not household_row:
        raise RuntimeError("Kunne ikke opprette husholdning ved innlogging.")
    household_id = household_row["id"]

    client.table("household_members").insert(
        {
            "household_id": household_id,
            "user_id": user.id,
            "role": "owner",
        }
    ).execute()

    profile = _load_profile(client, user.id)
    if profile:
        client.table("user_profiles").update(
            {
                "display_name": display_name or profile.get("display_name") or label,
                "default_household_id": household_id,
            }
        ).eq("id", user.id).execute()
    else:
        client.table("user_profiles").insert(
            {
                "id": user.id,
                "display_name": display_name or label,
                "default_household_id": household_id,
            }
        ).execute()

    return household_id


def sign_up(email: str, password: str, display_name: str, household_name: str) -> UserContext:
    client = get_supabase_anon()
    if client is None:
        raise RuntimeError("Supabase er ikke konfigurert.")

    try:
        auth_response = client.auth.sign_up(
            {
                "email": email.strip(),
                "password": password,
                "options": {"data": {"display_name": display_name.strip()}},
            }
        )
    except Exception as exc:
        _raise_auth_error(exc)
    if auth_response.user is None:
        raise RuntimeError("Kunne ikke opprette bruker.")

    if auth_response.session is None:
        raise RuntimeError(
            "Bruker opprettet. Bekreft e-posten din, logg deretter inn — "
            "husholdning og profil opprettes automatisk ved første innlogging."
        )

    authed = get_authenticated_client(
        auth_response.session.access_token,
        auth_response.session.refresh_token,
    )
    household_id = ensure_user_provisioned(authed, auth_response.user, display_name.strip())
    authed.table("households").update({"name": household_name.strip()}).eq("id", household_id).execute()

    return _build_context(
        auth_response.session,
        auth_response.user,
        household_id,
        display_name.strip(),
    )


def sign_in(email: str, password: str) -> UserContext:
    client = get_supabase_anon()
    if client is None:
        raise RuntimeError("Supabase er ikke konfigurert.")

    try:
        auth_response = client.auth.sign_in_with_password(
            {"email": email.strip(), "password": password}
        )
    except Exception as exc:
        _raise_auth_error(exc)
    if auth_response.session is None or auth_response.user is None:
        raise RuntimeError("Ugyldig e-post eller passord.")

    authed = get_authenticated_client(
        auth_response.session.access_token,
        auth_response.session.refresh_token,
    )
    display_name = _extract_display_name(auth_response.user)
    household_id = ensure_user_provisioned(authed, auth_response.user, display_name)
    profile = _load_profile(authed, auth_response.user.id)

    return _build_context(
        auth_response.session,
        auth_response.user,
        household_id,
        profile.get("display_name") or display_name,
    )


def build_context_from_tokens(access_token: str, refresh_token: str) -> UserContext:
    """Rebuild UserContext from stored tokens (FastAPI / Next.js clients)."""
    original_refresh = refresh_token.strip()
    cached = _lookup_token_rotation(original_refresh)
    if cached:
        access_token, refresh_token = cached

    client = get_authenticated_client(access_token, refresh_token)
    user = None

    try:
        user_response = client.auth.get_user()
        user = user_response.user if user_response else None
    except Exception as exc:
        message = str(getattr(exc, "message", None) or exc).lower()
        if "expired" not in message and "invalid jwt" not in message:
            _raise_auth_error(exc)

    if user is None:
        with _refresh_lock:
            cached = _lookup_token_rotation(original_refresh)
            if cached:
                access_token, refresh_token = cached
                client = get_authenticated_client(access_token, refresh_token)
                try:
                    user_response = client.auth.get_user()
                    user = user_response.user if user_response else None
                except Exception as exc:
                    message = str(getattr(exc, "message", None) or exc).lower()
                    if "expired" not in message and "invalid jwt" not in message:
                        _raise_auth_error(exc)

            if user is None:
                try:
                    refreshed = client.auth.refresh_session()
                except Exception as exc:
                    message = str(getattr(exc, "message", None) or exc).lower()
                    if "already used" in message:
                        recovered = _lookup_token_rotation(original_refresh)
                        if recovered:
                            access_token, refresh_token = recovered
                            client = get_authenticated_client(access_token, refresh_token)
                            user_response = client.auth.get_user()
                            user = user_response.user if user_response else None
                        if user is None:
                            _raise_auth_error(exc)
                    else:
                        _raise_auth_error(exc)
                else:
                    session = getattr(refreshed, "session", None)
                    user = getattr(refreshed, "user", None)
                    if session is None or user is None:
                        raise RuntimeError("Sesjonen er utløpt. Logg inn på nytt.")

                    access_token = session.access_token
                    refresh_token = session.refresh_token or original_refresh
                    client.auth.set_session(access_token, refresh_token)
                    client.postgrest.auth(access_token)
                    _cache_token_rotation(original_refresh, access_token, refresh_token)

                    from app.services.auth_context import mark_refreshed_tokens

                    mark_refreshed_tokens(access_token, refresh_token)

    display_name = _extract_display_name(user)
    household_id = _find_household_id(client, user.id)
    if not household_id:
        household_id = ensure_user_provisioned(client, user, display_name)

    profile = _load_profile(client, user.id)
    session = type("Session", (), {"access_token": access_token, "refresh_token": refresh_token})()

    return _build_context(
        session,
        user,
        household_id,
        profile.get("display_name") or display_name,
    )


def context_to_response(context: UserContext) -> dict:
    return {
        "user_id": context.user_id,
        "email": context.email,
        "household_id": context.household_id,
        "display_name": context.display_name,
        "assistant_name": context.assistant_name,
        "access_token": context.access_token,
        "refresh_token": context.refresh_token,
    }
