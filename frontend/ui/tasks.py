"""Tasks page — create tasks and display the task list."""

import streamlit as st

from app.services.action_engine import complete_task, create_task
from app.services.storage_service import list_records
from frontend.components.record_helpers import build_record_options
from frontend.components.visibility_helpers import visibility_badge, visibility_selectbox


def render_tasks() -> None:
    """Render the Oppgaver (Tasks) page."""
    st.subheader("Oppgaver")

    assets = list_records("assets")
    projects = list_records("projects")
    tasks = list_records("tasks")
    asset_options = build_record_options(assets, "name")
    project_options = build_record_options(projects, "name")

    with st.form("task_form"):
        title = st.text_input("Tittel")
        description = st.text_area("Beskrivelse")
        due_date = st.date_input("Frist", value=None)
        priority = st.slider("Prioritet", 1, 3, 2)
        asset_name = st.selectbox("Knytt til eiendel", list(asset_options.keys()))
        project_name = st.selectbox("Knytt til prosjekt", list(project_options.keys()))
        visibility = visibility_selectbox(key="task_visibility")
        submitted = st.form_submit_button("Opprett oppgave")

    if submitted and title.strip():
        create_task(
            {
                "title": title.strip(),
                "description": description or None,
                "due_date": due_date.isoformat() if due_date else None,
                "priority": priority,
                "asset_id": asset_options[asset_name],
                "project_id": project_options[project_name],
                "status": "open",
                "visibility": visibility,
            }
        )
        st.rerun()

    for task in tasks:
        with st.container(border=True):
            st.write(f"**{task['title']}**")
            st.caption(
                f"Prioritet {task.get('priority', 2)} · Status: {task.get('status', 'open')} · "
                f"{visibility_badge(task)}"
            )
            if task.get("description"):
                st.write(task["description"])
            if not task.get("completed") and st.button(
                "Marker som fullført", key=f"complete_{task['id']}"
            ):
                complete_task(task["id"])
                st.rerun()
