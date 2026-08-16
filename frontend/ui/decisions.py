"""Decisions page — create and manage decisions."""

import streamlit as st

from app.services.action_engine import create_decision, finalize_decision
from app.services.storage_service import list_records
from frontend.components.record_helpers import build_record_options
from frontend.components.visibility_helpers import visibility_selectbox


def render_decisions() -> None:
    """Render the Beslutninger (Decisions) page."""
    st.subheader("Beslutninger")

    assets = list_records("assets")
    projects = list_records("projects")
    decisions = list_records("decisions")
    asset_options = build_record_options(assets, "name")
    project_options = build_record_options(projects, "name")

    with st.form("decision_form"):
        title = st.text_input("Tittel")
        summary = st.text_area("Beskrivelse")
        status = st.selectbox("Status", ["open", "decided", "paused"])
        next_action = st.text_input("Neste handling")
        asset_name = st.selectbox(
            "Knytt til eiendel", list(asset_options.keys()), key="decision_asset"
        )
        project_name = st.selectbox(
            "Knytt til prosjekt", list(project_options.keys()), key="decision_project"
        )
        visibility = visibility_selectbox(key="decision_visibility")
        submitted = st.form_submit_button("Opprett beslutning")

    if submitted and title.strip():
        create_decision(
            {
                "title": title.strip(),
                "summary": summary or None,
                "status": status,
                "next_action": next_action or None,
                "asset_id": asset_options[asset_name],
                "project_id": project_options[project_name],
                "visibility": visibility,
            }
        )
        st.rerun()

    for decision in decisions:
        with st.container(border=True):
            st.write(f"**{decision['title']}**")
            st.caption(f"Status: {decision.get('status', 'open')}")
            if decision.get("summary"):
                st.write(decision["summary"])
            if decision.get("status") != "decided" and st.button(
                "Marker som besluttet", key=f"decide_{decision['id']}"
            ):
                finalize_decision(decision["id"])
                st.rerun()
