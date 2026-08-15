"""Authentication UI — login, registration, and profile management."""

from __future__ import annotations

import streamlit as st

from app.services.auth_service import (
    get_user_profile,
    login,
    logout,
    register,
    update_user_profile,
)


# ---------------------------------------------------------------------------
# Public helpers called from the main streamlit_app
# ---------------------------------------------------------------------------


def is_authenticated() -> bool:
    """Return True if a user is currently logged in."""
    return bool(st.session_state.get("auth_user"))


def get_current_user_id() -> str | None:
    """Return the Supabase user-id of the logged-in user, or None."""
    user = st.session_state.get("auth_user")
    return user.id if user else None


def get_current_profile() -> dict:
    """Return cached profile dict for the logged-in user (may be empty)."""
    return st.session_state.get("auth_profile") or {}


def render_auth_gate() -> bool:
    """Show login/register forms when the user is not authenticated.

    Returns True if the user is (now) authenticated, False otherwise.
    If True is returned the caller should render the main application.
    """
    if is_authenticated():
        return True

    st.title("WilliamOS")
    tab_login, tab_register = st.tabs(["Logg inn", "Registrer deg"])

    with tab_login:
        _render_login_form()

    with tab_register:
        _render_register_form()

    return is_authenticated()


def render_auth_sidebar() -> None:
    """Render user-info and logout button inside an existing sidebar block."""
    profile = get_current_profile()
    user = st.session_state.get("auth_user")

    display_name = profile.get("name") or (user.email if user else "Bruker")
    assistant = profile.get("assistant_name") or "Jarvis"

    st.markdown(f"👤 **{display_name}**")
    st.caption(f"Assistent: {assistant}")
    if user:
        st.caption(user.email)

    if st.button("Logg ut", key="sidebar_logout"):
        _do_logout()
        st.rerun()


def render_profile_page() -> None:
    """Full profile-management page."""
    st.subheader("Min profil")

    user = st.session_state.get("auth_user")
    if user is None:
        st.warning("Ikke innlogget.")
        return

    profile = get_current_profile()

    with st.form("profile_form"):
        name = st.text_input("Navn", value=profile.get("name") or "")
        age = st.number_input(
            "Alder",
            min_value=0,
            max_value=150,
            value=int(profile.get("age") or 0),
            step=1,
        )
        assistant_name = st.text_input(
            "Navn på assistent",
            value=profile.get("assistant_name") or "Jarvis",
            help="Hva vil du kalle din personlige assistent? F.eks. Jarvis, ARIA, ...",
        )
        submitted = st.form_submit_button("Lagre")

    if submitted:
        try:
            updated = update_user_profile(
                user.id,
                {
                    "name": name,
                    "age": int(age) if age else None,
                    "assistant_name": assistant_name,
                },
            )
            if updated:
                st.session_state["auth_profile"] = updated
                st.success("Profil oppdatert!")
            else:
                st.warning("Ingen endringer ble lagret.")
        except Exception as exc:
            st.error(f"Feil ved lagring: {exc}")


# ---------------------------------------------------------------------------
# Internal form renderers
# ---------------------------------------------------------------------------


def _render_login_form() -> None:
    with st.form("login_form"):
        st.markdown("### Logg inn")
        email = st.text_input("E-post", key="login_email")
        password = st.text_input("Passord", type="password", key="login_password")
        submitted = st.form_submit_button("Logg inn")

    if submitted:
        if not email or not password:
            st.error("Fyll inn e-post og passord.")
            return
        try:
            result = login(email, password)
            _store_session(result)
            st.success("Du er nå logget inn!")
            st.rerun()
        except Exception as exc:
            st.error(f"Innlogging feilet: {exc}")


def _render_register_form() -> None:
    with st.form("register_form"):
        st.markdown("### Opprett konto")
        email = st.text_input("E-post", key="reg_email")
        password = st.text_input("Passord", type="password", key="reg_password")
        password2 = st.text_input(
            "Bekreft passord", type="password", key="reg_password2"
        )
        st.divider()
        name = st.text_input("Navn (valgfritt)", key="reg_name")
        age = st.number_input(
            "Alder (valgfritt)", min_value=0, max_value=150, value=0, step=1,
            key="reg_age",
        )
        assistant_name = st.text_input(
            "Navn på assistent",
            value="Jarvis",
            key="reg_assistant",
            help="Hva vil du kalle din personlige assistent? F.eks. Jarvis, ARIA, ...",
        )
        submitted = st.form_submit_button("Registrer")

    if submitted:
        if not email or not password:
            st.error("Fyll inn e-post og passord.")
            return
        if len(password) < 6:
            st.error("Passordet må være minst 6 tegn.")
            return
        if password != password2:
            st.error("Passordene stemmer ikke overens.")
            return
        try:
            result = register(
                email,
                password,
                name=name,
                age=int(age) if age else None,
                assistant_name=assistant_name or "Jarvis",
            )
            _store_session(result)
            if result.get("session") is None:
                st.info(
                    "Konto opprettet! Sjekk e-posten din for å bekrefte kontoen, "
                    "og logg deretter inn."
                )
            else:
                st.success("Konto opprettet og du er nå logget inn!")
                st.rerun()
        except Exception as exc:
            st.error(f"Registrering feilet: {exc}")


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------


def _store_session(auth_result: dict) -> None:
    """Persist auth result into Streamlit session_state."""
    st.session_state["auth_user"] = auth_result.get("user")
    st.session_state["auth_session"] = auth_result.get("session")
    # Eagerly load profile so it's ready for the sidebar
    user = auth_result.get("user")
    if user:
        try:
            profile = get_user_profile(user.id)
            st.session_state["auth_profile"] = profile or {}
        except Exception:
            st.session_state["auth_profile"] = {}


def _do_logout() -> None:
    try:
        logout()
    except Exception:
        pass
    st.session_state.pop("auth_user", None)
    st.session_state.pop("auth_session", None)
    st.session_state.pop("auth_profile", None)
    st.session_state.pop("messages", None)
