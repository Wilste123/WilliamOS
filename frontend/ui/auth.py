"""Authentication page — sign up and sign in."""

import streamlit as st

from app.services.auth_service import save_session_to_state, sign_in, sign_up


def render_auth() -> None:
    """Render login and signup forms."""
    st.subheader("Logg inn på WilliamOS")
    st.caption("Private ting er bare dine. Delte ting synes for hele husholdningen.")

    tab_login, tab_signup = st.tabs(["Logg inn", "Opprett konto"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("E-post", key="login_email")
            password = st.text_input("Passord", type="password", key="login_password")
            submitted = st.form_submit_button("Logg inn", type="primary")

        if submitted:
            try:
                context = sign_in(email, password)
                save_session_to_state(context)
                st.success("Innlogget!")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))

    with tab_signup:
        with st.form("signup_form"):
            display_name = st.text_input("Navn")
            household_name = st.text_input("Husholdningsnavn", value="Min husholdning")
            email = st.text_input("E-post", key="signup_email")
            password = st.text_input("Passord", type="password", key="signup_password")
            submitted = st.form_submit_button("Opprett konto", type="primary")

        if submitted:
            try:
                context = sign_up(email, password, display_name, household_name)
                save_session_to_state(context)
                st.success("Konto opprettet og innlogget!")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))
