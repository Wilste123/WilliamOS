"""Chat page — PA chat interface backed by the agent service."""

import streamlit as st

from app.agents.pa_agent import ask_agent


def render_chat() -> None:
    """Render the PA-chat page.

    Conversation history is stored in ``st.session_state.messages`` so the
    context persists across reruns within the same browser session.
    """
    st.subheader("PA-chat")

    use_documents = st.toggle(
        "Bruk opplastede dokumenter",
        value=True,
        help="La chatten søke i dokumenter lastet opp fra alle moduler",
    )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                with st.expander("📎 Kilder brukt", expanded=False):
                    for src in msg["sources"]:
                        st.caption(
                            f"**{src['filename']}** "
                            f"(modul: {src.get('source_module') or 'ukjent'}) "
                            f"— score: {src['score']:.2f}"
                        )
                        if src.get("snippet"):
                            st.text(src["snippet"][:300])

    prompt = st.chat_input("Hva trenger du hjelp med?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("WilliamOS tenker..."):
                answer, sources = ask_agent(
                    prompt,
                    use_documents=use_documents,
                    history=st.session_state.messages[:-1],
                )
            st.write(answer)
            if sources:
                with st.expander("📎 Kilder brukt", expanded=False):
                    for src in sources:
                        st.caption(
                            f"**{src['filename']}** "
                            f"(modul: {src.get('source_module') or 'ukjent'}) "
                            f"— score: {src['score']:.2f}"
                        )
                        if src.get("snippet"):
                            st.text(src["snippet"][:300])

        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "sources": sources}
        )
