"""Dashboard page — renders metrics, priorities, events, and recent activity."""

import streamlit as st

from app.services.action_engine import build_dashboard_summary
from frontend.components.record_helpers import render_collection


def render_dashboard() -> None:
    """Render the Dashboard page."""
    st.subheader("Dashboard")
    dashboard = build_dashboard_summary()
    metrics = dashboard["metrics"]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Eiendeler", metrics["assets"])
    col2.metric("Åpne oppgaver", metrics["open_tasks"])
    col3.metric("Aktive prosjekter", metrics["projects"])
    col4.metric("Dokumenter", metrics["documents"])
    col5.metric("Åpne beslutninger", metrics["open_decisions"])

    st.markdown("### Prioriteter denne uka")
    render_collection(dashboard["priorities"], ["title", "priority", "due_date", "status"])

    st.markdown("### Kommende hendelser")
    render_collection(dashboard["upcoming_events"], ["title", "event_date", "event_type"])

    st.markdown("### Aktive prosjekter")
    render_collection(dashboard["active_projects"], ["name", "status", "next_action"])

    st.markdown("### Nye dokumenter")
    render_collection(dashboard["new_documents"], ["filename", "created_at"])

    st.markdown("### Nylig aktivitet")
    render_collection(dashboard["recent_activity"], ["title", "event_type", "created_at"])
