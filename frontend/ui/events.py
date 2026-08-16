"""Events page — log and view events (maintenance, meetings, deadlines, etc.)."""

import streamlit as st

from app.services.action_engine import create_event
from app.services.storage_service import list_records
from frontend.components.record_helpers import build_record_options, render_collection
from frontend.components.visibility_helpers import visibility_selectbox


def render_events() -> None:
    """Render the Hendelser (Events) page."""
    st.subheader("Hendelser")

    assets = list_records("assets")
    projects = list_records("projects")
    decisions = list_records("decisions")
    events = list_records("events")
    asset_options = build_record_options(assets, "name")
    project_options = build_record_options(projects, "name")
    decision_options = build_record_options(decisions, "title")

    with st.form("event_form"):
        title = st.text_input("Tittel")
        event_type = st.selectbox(
            "Type", ["general", "maintenance", "meeting", "deadline", "purchase"]
        )
        event_date = st.date_input("Dato", value=None)
        notes = st.text_area("Notater")
        asset_name = st.selectbox(
            "Knytt til eiendel", list(asset_options.keys()), key="event_asset"
        )
        project_name = st.selectbox(
            "Knytt til prosjekt", list(project_options.keys()), key="event_project"
        )
        decision_name = st.selectbox(
            "Knytt til beslutning", list(decision_options.keys()), key="event_decision"
        )
        visibility = visibility_selectbox(key="event_visibility")
        submitted = st.form_submit_button("Logg hendelse")

    if submitted and title.strip():
        create_event(
            {
                "title": title.strip(),
                "event_type": event_type,
                "event_date": event_date.isoformat() if event_date else None,
                "notes": notes or None,
                "asset_id": asset_options[asset_name],
                "project_id": project_options[project_name],
                "decision_id": decision_options[decision_name],
                "visibility": visibility,
            }
        )
        st.rerun()

    render_collection(events, ["title", "event_type", "event_date", "created_at"])
