from __future__ import annotations

import streamlit as st

from app.services.auth_context import UserContext, get_current_context, set_current_context
from app.services import auth_core

SESSION_KEY = "auth_session"


def sign_up(email: str, password: str, display_name: str, household_name: str) -> UserContext:
    return auth_core.sign_up(email, password, display_name, household_name)


def sign_in(email: str, password: str) -> UserContext:
    return auth_core.sign_in(email, password)


def sign_out() -> None:
    from app.database.supabase import get_supabase_anon

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
