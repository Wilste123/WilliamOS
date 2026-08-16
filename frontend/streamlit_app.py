"""WilliamOS Streamlit entrypoint.

This file is intentionally thin.  Its only responsibilities are:
1. Configure the Streamlit page.
2. Render the sidebar navigation.
3. Dispatch to the correct page-render function from ``frontend.ui``.

All business logic lives in ``app/services`` and ``app/agents``.
All Streamlit rendering per page lives in ``frontend/ui/<page>.py``.
Shared UI helpers (record option builders, collection renderers) live in
``frontend/components/record_helpers.py``.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import streamlit as st

from app.services.auth_service import is_authenticated, restore_session_from_state, sign_out
from app.services.profile_service import get_assistant_name
from frontend.ui.assets import render_assets
from frontend.ui.auth import render_auth
from frontend.ui.chat import render_chat
from frontend.ui.dashboard import render_dashboard
from frontend.ui.decisions import render_decisions
from frontend.ui.documents import render_documents
from frontend.ui.events import render_events
from frontend.ui.inbox import render_inbox
from frontend.ui.memory import render_memory
from frontend.ui.projects import render_projects
from frontend.ui.self_evolve import render_self_evolve
from frontend.ui.settings import render_settings
from frontend.ui.tasks import render_tasks
from frontend.ui.timeline import render_timeline

st.set_page_config(page_title="WilliamOS", page_icon="🧠", layout="wide")

if not is_authenticated():
    st.title("WilliamOS")
    render_auth()
    st.stop()

context = restore_session_from_state()
assistant_name = get_assistant_name()

st.title("WilliamOS")
st.caption(f"Din assistent: {assistant_name}")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    if context:
        st.write(f"**{context.display_name or context.email}**")
        st.caption(f"Husholdning: {context.household_id[:8]}…")
    if st.button("Logg ut"):
        sign_out()
        st.rerun()

    st.header("Navigasjon")
    page = st.radio(
        "Velg",
        [
            "Dashboard",
            "Inbox",
            "Chat",
            "Oppgaver",
            "Eiendeler",
            "Prosjekter",
            "Beslutninger",
            "Hendelser",
            "Dokumenter",
            "Timeline",
            "Minne",
            "Innstillinger",
            "self-evolve",
        ],
    )
    st.divider()
    st.caption("Byggesteiner: inbox, assets, tasks, decisions, timeline.")

_PAGE_RENDERERS = {
    "Dashboard": render_dashboard,
    "Inbox": render_inbox,
    "Chat": render_chat,
    "Oppgaver": render_tasks,
    "Eiendeler": render_assets,
    "Prosjekter": render_projects,
    "Beslutninger": render_decisions,
    "Hendelser": render_events,
    "Dokumenter": render_documents,
    "Timeline": render_timeline,
    "Minne": render_memory,
    "Innstillinger": render_settings,
    "self-evolve": render_self_evolve,
}

renderer = _PAGE_RENDERERS.get(page)
if renderer:
    renderer()
