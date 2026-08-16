"""Settings page — personalize assistant name and preferences."""

import streamlit as st

from app.services.auth_context import get_current_context
from app.services.profile_service import DEFAULT_ASSISTANT_NAME, get_assistant_name, update_assistant_name
from app.services.auth_service import save_session_to_state


def render_settings() -> None:
    """Render user settings."""
    st.subheader("Innstillinger")

    context = get_current_context()
    current_name = get_assistant_name()

    st.markdown("### Assistentnavn")
    st.write(
        "Gi assistenten et navn du liker — for eksempel **Jarvis**, **Ada** eller **WilliamOS**."
    )

    with st.form("assistant_name_form"):
        assistant_name = st.text_input(
            "Assistentnavn",
            value=current_name,
            placeholder=DEFAULT_ASSISTANT_NAME,
        )
        submitted = st.form_submit_button("Lagre navn", type="primary")

    if submitted:
        saved_name = update_assistant_name(assistant_name)
        if context:
            save_session_to_state(
                context.__class__(
                    user_id=context.user_id,
                    email=context.email,
                    household_id=context.household_id,
                    access_token=context.access_token,
                    refresh_token=context.refresh_token,
                    display_name=context.display_name,
                    assistant_name=saved_name,
                )
            )
        st.success(f"Assistenten heter nå {saved_name}.")
        st.rerun()

    st.caption(f"Nåværende navn: **{current_name}**")
