"""Memory page — store and review facts the agent should know."""

import streamlit as st

from app.services.memory_service import get_recent_memory_text, save_memory


def render_memory() -> None:
    """Render the Minne (Memory) page."""
    st.subheader("Minne")
    st.write("Her kan du lagre fakta agenten skal vite.")

    with st.form("memory_form"):
        key = st.text_input("Nøkkel", placeholder="f.eks. bil")
        category = st.text_input("Kategori", placeholder="asset, project, personal")
        value = st.text_area("Hva skal huskes?")
        submitted = st.form_submit_button("Lagre minne")

    if submitted and value:
        result = save_memory(value=value, key=key or None, category=category or None)
        st.success(f"Lagret: {result['mode']}")

    st.markdown("### Lagret kontekst")
    st.text(get_recent_memory_text())
