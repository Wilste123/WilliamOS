"""Inbox page — capture free-text notes and apply suggestions."""

import streamlit as st

from app.services.action_engine import apply_inbox_suggestion, capture_inbox_entry
from app.services.storage_service import list_records

_OBJECT_LABELS = {
    "asset": "Eiendel",
    "task": "Oppgave",
    "decision": "Beslutning",
    "project": "Prosjekt",
}


def _suggestion_label(suggestion: dict) -> str:
    object_type = suggestion.get("object_type", "unknown")
    fields = suggestion.get("fields") or {}
    name = fields.get("name") or fields.get("title") or object_type
    return f"{_OBJECT_LABELS.get(object_type, object_type)}: {name}"


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
        capture_inbox_entry(inbox_text.strip())
        st.success("Lagret i inbox")
        st.rerun()

    st.markdown("### Ventende inbox-signaler")
    inbox_items = [item for item in list_records("inbox_items") if item.get("status") != "processed"]

    if not inbox_items:
        st.info("Ingen ventende inbox-signaler.")
        return

    for item in inbox_items:
        with st.container(border=True):
            st.write(f"**{item['text']}**")
            st.caption(f"Status: {item.get('status', 'captured')}")

            suggestions = item.get("suggestions") or []
            if not suggestions:
                st.caption("Ingen forslag for dette signalet.")
                continue

            for index, suggestion in enumerate(suggestions):
                col1, col2 = st.columns([4, 1])
                col1.write(_suggestion_label(suggestion))
                if col2.button("Opprett", key=f"apply_{item['id']}_{index}"):
                    result = apply_inbox_suggestion(item["id"], index)
                    created = result["created"]
                    label = created.get("name") or created.get("title") or result["object_type"]
                    st.success(f"Opprettet: {label}")
                    st.rerun()
