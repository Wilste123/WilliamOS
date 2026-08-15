"""Self-evolve page — view logged requests and top recurring signals."""

import streamlit as st

from app.agents.self_evolve import analyze_requests_locally


def render_self_evolve() -> None:
    """Render the self-evolve page."""
    st.subheader("self-evolve signaler")
    st.write("Dette er v0.1: vi logger spørsmål og ser hvilke behov som gjentar seg.")

    analysis = analyze_requests_locally()
    st.metric("Antall forespørsler logget", analysis["count"])

    st.markdown("### Toppsignaler")
    if analysis["top_signals"]:
        st.write(analysis["top_signals"])
    else:
        st.info("Ingen signaler enda. Bruk chatten først.")
