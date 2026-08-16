"""Projects page — create, edit and view projects."""

import streamlit as st

from app.services.action_engine import create_project, update_project
from app.services.storage_service import list_records
from frontend.components.record_helpers import build_record_options
from frontend.components.visibility_helpers import visibility_selectbox, render_collection


def render_projects() -> None:
    """Render the Prosjekter (Projects) page."""
    st.subheader("Prosjekter")

    assets = list_records("assets")
    projects = list_records("projects")
    asset_options = build_record_options(assets, "name")

    with st.expander("Opprett nytt prosjekt", expanded=not projects):
        with st.form("project_form"):
            name = st.text_input("Prosjektnavn")
            status = st.selectbox("Status", ["active", "on_hold", "done"])
            next_action = st.text_input("Neste handling")
            notes = st.text_area("Notater")
            asset_name = st.selectbox(
                "Knytt til eiendel", list(asset_options.keys()), key="project_asset"
            )
            visibility = visibility_selectbox(key="project_visibility")
            submitted = st.form_submit_button("Opprett prosjekt")

        if submitted and name.strip():
            create_project(
                {
                    "name": name.strip(),
                    "status": status,
                    "next_action": next_action or None,
                    "notes": notes or None,
                    "asset_id": asset_options[asset_name],
                    "visibility": visibility,
                }
            )
            st.rerun()

    for project in projects:
        with st.container(border=True):
            st.write(f"**{project['name']}**")
            st.caption(f"Status: {project.get('status', 'active')}")
            if project.get("next_action"):
                st.write(f"Neste: {project['next_action']}")
            if project.get("notes"):
                st.write(project["notes"])

            with st.expander("Rediger prosjekt"):
                with st.form(f"edit_project_{project['id']}"):
                    new_status = st.selectbox(
                        "Status",
                        ["active", "on_hold", "done"],
                        index=max(
                            0,
                            ["active", "on_hold", "done"].index(project.get("status", "active"))
                            if project.get("status", "active") in ["active", "on_hold", "done"]
                            else 0,
                        ),
                        key=f"status_{project['id']}",
                    )
                    new_next = st.text_input(
                        "Neste handling",
                        value=project.get("next_action") or "",
                        key=f"next_{project['id']}",
                    )
                    new_notes = st.text_area(
                        "Notater",
                        value=project.get("notes") or "",
                        key=f"notes_{project['id']}",
                    )
                    if st.form_submit_button("Lagre endringer"):
                        update_project(
                            project["id"],
                            {
                                "status": new_status,
                                "next_action": new_next or None,
                                "notes": new_notes or None,
                            },
                        )
                        st.rerun()

    if not projects:
        st.info("Ingen prosjekter ennå.")
