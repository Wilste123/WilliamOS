"""Inbox page — capture free-text notes and display recent inbox items."""

import streamlit as st

from app.services.action_engine import capture_inbox_entry
from app.services.storage_service import list_records
from frontend.components.record_helpers import render_collection


def render_inbox() -> None:
    """Render the Inbox page."""
    st.subheader("Inbox")

    with st.form("inbox_form"):
        inbox_text = st.text_area(
            "Skriv noe du vil fange opp",
            placeholder="Vurderer å kjøpe Pioner 320 til 25 000",
        )
        submitted = st.form_submit_button("Legg i inbox")

    if submitted and inbox_text.strip():
        captured = capture_inbox_entry(inbox_text.strip())
        st.success("Lagret i inbox")
        st.json(captured)

    st.markdown("### Siste inbox-signaler")
    render_collection(list_records("inbox_items"), ["text", "status", "created_at"])
