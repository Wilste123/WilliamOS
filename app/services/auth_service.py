from __future__ import annotations

import streamlit as st

from app.database.supabase import get_authenticated_client, get_supabase_anon, response_data
from app.services.auth_context import UserContext, get_current_context, set_current_context

SESSION_KEY = "auth_session"


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
    """Return the first row from a Supabase list response."""
    rows = response_data(response, []) or []
    if not rows:
        return default
    return rows[0]


def _load_profile(client, user_id: str) -> dict:
    """Load core profile fields needed for auth/household setup."""
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


def _ensure_user_provisioned(client, user, display_name: str | None = None) -> str:
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

    auth_response = client.auth.sign_up(
        {
            "email": email.strip(),
            "password": password,
            "options": {"data": {"display_name": display_name.strip()}},
        }
    )
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
    household_id = _ensure_user_provisioned(authed, auth_response.user, display_name.strip())
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

    auth_response = client.auth.sign_in_with_password(
        {"email": email.strip(), "password": password}
    )
    if auth_response.session is None or auth_response.user is None:
        raise RuntimeError("Ugyldig e-post eller passord.")

    authed = get_authenticated_client(
        auth_response.session.access_token,
        auth_response.session.refresh_token,
    )
    display_name = _extract_display_name(auth_response.user)
    household_id = _ensure_user_provisioned(authed, auth_response.user, display_name)
    profile = _load_profile(authed, auth_response.user.id)

    return _build_context(
        auth_response.session,
        auth_response.user,
        household_id,
        profile.get("display_name") or display_name,
    )


def sign_out() -> None:
    client = get_supabase_anon()
    if client is not None:
        try:
            client.auth.sign_out()
        except Exception:
            pass
    if SESSION_KEY in st.session_state:
        del st.session_state[SESSION_KEY]
    set_current_context(None)


def save_session_to_state(context: UserContext) -> None:
    st.session_state[SESSION_KEY] = {
        "user_id": context.user_id,
        "email": context.email,
        "household_id": context.household_id,
        "access_token": context.access_token,
        "refresh_token": context.refresh_token,
        "display_name": context.display_name,
        "assistant_name": context.assistant_name,
    }
    set_current_context(context)


def restore_session_from_state() -> UserContext | None:
    if SESSION_KEY not in st.session_state:
        set_current_context(None)
        return None

    data = st.session_state[SESSION_KEY]
    context = UserContext(
        user_id=data["user_id"],
        email=data["email"],
        household_id=data["household_id"],
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        display_name=data.get("display_name"),
        assistant_name=data.get("assistant_name"),
    )
    set_current_context(context)
    return context


def is_authenticated() -> bool:
    if get_current_context() is not None:
        return True
    return restore_session_from_state() is not None


def get_active_context() -> UserContext:
    context = get_current_context()
    if context is not None:
        return context
    restored = restore_session_from_state()
    if restored is not None:
        return restored
    raise RuntimeError("Du må være innlogget for å utføre denne handlingen.")
