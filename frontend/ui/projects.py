"""Projects page — create and view projects."""

import streamlit as st

from app.services.action_engine import create_project
from app.services.storage_service import list_records
from frontend.components.record_helpers import build_record_options, render_collection


def render_projects() -> None:
    """Render the Prosjekter (Projects) page."""
    st.subheader("Prosjekter")

    assets = list_records("assets")
    projects = list_records("projects")
    asset_options = build_record_options(assets, "name")

    with st.form("project_form"):
        name = st.text_input("Prosjektnavn")
        status = st.selectbox("Status", ["active", "on_hold", "done"])
        next_action = st.text_input("Neste handling")
        notes = st.text_area("Notater")
        asset_name = st.selectbox(
            "Knytt til eiendel", list(asset_options.keys()), key="project_asset"
        )
        submitted = st.form_submit_button("Opprett prosjekt")

    if submitted and name.strip():
        create_project(
            {
                "name": name.strip(),
                "status": status,
                "next_action": next_action or None,
                "notes": notes or None,
                "asset_id": asset_options[asset_name],
            }
        )
        st.rerun()

    render_collection(projects, ["name", "status", "next_action", "created_at"])
