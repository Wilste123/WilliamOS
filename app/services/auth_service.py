from __future__ import annotations

import streamlit as st

from app.database.supabase import get_authenticated_client, get_supabase_anon
from app.services.auth_context import UserContext, get_current_context, set_current_context

SESSION_KEY = "auth_session"


def _build_context(session, user, household_id: str, display_name: str | None = None) -> UserContext:
    return UserContext(
        user_id=user.id,
        email=user.email or "",
        household_id=household_id,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        display_name=display_name,
    )


def _resolve_household_id(client, user_id: str) -> str:
    profile = (
        client.table("user_profiles")
        .select("default_household_id")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    if profile.data and profile.data.get("default_household_id"):
        return profile.data["default_household_id"]

    membership = (
        client.table("household_members")
        .select("household_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if membership.data:
        return membership.data[0]["household_id"]

    raise RuntimeError("Fant ingen husholdning for brukeren. Kontakt administrator.")


def _load_profile_name(client, user_id: str) -> str | None:
    profile = (
        client.table("user_profiles")
        .select("display_name")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    if profile.data:
        return profile.data.get("display_name")
    return None


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
            "Bruker opprettet. Bekreft e-posten din i Supabase hvis e-postbekreftelse er påslått, "
            "og logg inn etterpå."
        )

    authed = get_authenticated_client(
        auth_response.session.access_token,
        auth_response.session.refresh_token,
    )
    household = (
        authed.table("households")
        .insert({"name": household_name.strip(), "created_by": auth_response.user.id})
        .execute()
    )
    household_id = household.data[0]["id"]

    authed.table("household_members").insert(
        {
            "household_id": household_id,
            "user_id": auth_response.user.id,
            "role": "owner",
        }
    ).execute()
    authed.table("user_profiles").insert(
        {
            "id": auth_response.user.id,
            "display_name": display_name.strip(),
            "default_household_id": household_id,
        }
    ).execute()

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
    household_id = _resolve_household_id(authed, auth_response.user.id)
    display_name = _load_profile_name(authed, auth_response.user.id)

    return _build_context(
        auth_response.session,
        auth_response.user,
        household_id,
        display_name,
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
