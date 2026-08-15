"""Timeline page — chronological event log."""

import streamlit as st

from app.services.action_engine import build_timeline
from frontend.components.record_helpers import render_collection


def render_timeline() -> None:
    """Render the Timeline page."""
    st.subheader("Timeline")
    timeline = build_timeline()
    render_collection(timeline, ["title", "event_type", "event_date", "created_at", "notes"])
