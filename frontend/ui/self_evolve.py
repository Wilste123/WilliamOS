"""Self-evolve page — view logged requests and top recurring signals."""

import streamlit as st

from app.agents.self_evolve import analyze_requests


def render_self_evolve() -> None:
    """Render the self-evolve page."""
    st.subheader("self-evolve signaler")
    st.write("Vi logger chat-forespørsler i Supabase og ser hvilke behov som gjentar seg.")

    analysis = analyze_requests()
    st.metric("Antall forespørsler logget", analysis["count"])

    st.markdown("### Toppsignaler")
    if analysis["top_signals"]:
        for keyword, count in analysis["top_signals"]:
            st.write(f"**{keyword}**: {count} ganger")
    else:
        st.info("Ingen signaler enda. Bruk chatten først.")
