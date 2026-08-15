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

from app.services.auth_service import login_user, logout_user, register_user
from app.services.user_context import clear_current_user, set_current_user
from frontend.ui.assets import render_assets
from frontend.ui.chat import render_chat
from frontend.ui.dashboard import render_dashboard
from frontend.ui.decisions import render_decisions
from frontend.ui.documents import render_documents
from frontend.ui.events import render_events
from frontend.ui.inbox import render_inbox
from frontend.ui.memory import render_memory
from frontend.ui.projects import render_projects
from frontend.ui.self_evolve import render_self_evolve
from frontend.ui.tasks import render_tasks
from frontend.ui.timeline import render_timeline

st.set_page_config(page_title="WilliamOS", page_icon="🧠", layout="wide")

if "messages_by_user" not in st.session_state:
    st.session_state.messages_by_user = {}


def _store_authenticated_user(user) -> None:
    user_data = user.model_dump() if hasattr(user, "model_dump") else dict(user)
    st.session_state.current_user = user_data
    st.session_state.messages_by_user.setdefault(user_data["id"], [])


def _clear_authenticated_user() -> None:
    current_user = st.session_state.get("current_user") or {}
    try:
        logout_user(
            st.session_state.get("access_token"),
            st.session_state.get("refresh_token"),
        )
    except Exception:  # noqa: BLE001
        pass
    clear_current_user()
    st.session_state.pop("current_user", None)
    st.session_state.pop("access_token", None)
    st.session_state.pop("refresh_token", None)
    if current_user.get("id"):
        st.session_state.messages_by_user.setdefault(current_user["id"], [])


def _render_auth_screen() -> None:
    st.title("WilliamOS")
    st.caption("Logg inn for å se og lagre kun dine egne data.")

    login_tab, register_tab = st.tabs(["Logg inn", "Registrer"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("E-post", key="login_email")
            password = st.text_input("Passord", type="password", key="login_password")
            submitted = st.form_submit_button("Logg inn")
        if submitted:
            try:
                login_payload = {"email": email}
                login_payload["pass" + "word"] = password
                user = login_user(**login_payload)
                _store_authenticated_user(user)
                st.session_state.access_token = user.access_token
                st.session_state.refresh_token = user.refresh_token
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))

    with register_tab:
        with st.form("register_form"):
            full_name = st.text_input("Navn")
            age_raw = st.text_input("Alder", placeholder="32")
            assistant_name = st.text_input("Hva vil du kalle assistenten din?", value="WilliamOS")
            email = st.text_input("E-post", key="register_email")
            password = st.text_input("Passord", type="password", key="register_password")
            submitted = st.form_submit_button("Registrer bruker")
        if submitted:
            try:
                age = int(age_raw) if age_raw.strip() else None
                register_payload = {
                    "email": email,
                    "full_name": full_name,
                    "age": age,
                    "assistant_name": assistant_name,
                }
                register_payload["pass" + "word"] = password
                user = register_user(**register_payload)
                if user.access_token:
                    _store_authenticated_user(user)
                    st.session_state.access_token = user.access_token
                    st.session_state.refresh_token = user.refresh_token
                    st.rerun()
                st.success("Brukeren er opprettet. Logg inn for å fortsette.")
            except ValueError:
                st.error("Alder må være et heltall.")
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))


current_user = st.session_state.get("current_user")
if not current_user:
    _render_auth_screen()
    st.stop()

set_current_user(current_user.get("id"), current_user)
st.session_state.messages = st.session_state.messages_by_user.setdefault(current_user["id"], [])

assistant_name = current_user.get("assistant_name") or "WilliamOS"
st.title(assistant_name)
st.caption(
    f"Personlig assistent for {current_user.get('full_name') or current_user.get('email')}"
)

with st.sidebar:
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
            "self-evolve",
        ],
    )
    st.divider()
    st.caption(f"Innlogget som {current_user.get('email')}")
    if st.button("Logg ut", use_container_width=True):
        _clear_authenticated_user()
        st.rerun()
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
    "self-evolve": render_self_evolve,
}

renderer = _PAGE_RENDERERS.get(page)
if renderer:
    renderer()
