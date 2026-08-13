import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import streamlit as st
from app.agents.pa_agent import ask_agent
from app.agents.self_evolve import analyze_requests_locally
from app.services.memory_service import save_memory, get_recent_memory_text
from app.services.document_service import save_uploaded_file

st.set_page_config(page_title="WilliamOS", page_icon="🧠", layout="wide")

st.title("WilliamOS")
st.caption("Mini-Jarvis prototype for HouseOS, LifeOS og self-evolve")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Navigasjon")
    page = st.radio("Velg", ["Chat", "Minne", "Dokumenter", "self-evolve"])
    st.divider()
    st.caption("Første mål: bruk dette daglig i 30 dager.")

if page == "Chat":
    st.subheader("PA-chat")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    prompt = st.chat_input("Hva trenger du hjelp med?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("WilliamOS tenker..."):
                answer = ask_agent(prompt)
            st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

elif page == "Minne":
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

elif page == "Dokumenter":
    st.subheader("Dokumenter")
    uploaded = st.file_uploader("Last opp PDF, bilde eller fil", type=None)
    if uploaded is not None:
        if st.button("Lagre dokument"):
            saved = save_uploaded_file(uploaded.name, uploaded.getvalue())
            st.success("Dokument lagret lokalt")
            st.json(saved)

elif page == "self-evolve":
    st.subheader("self-evolve signaler")
    st.write("Dette er v0.1: vi logger spørsmål og ser hvilke behov som gjentar seg.")
    analysis = analyze_requests_locally()
    st.metric("Antall forespørsler logget", analysis["count"])
    st.markdown("### Toppsignaler")
    if analysis["top_signals"]:
        st.write(analysis["top_signals"])
    else:
        st.info("Ingen signaler enda. Bruk chatten først.")
