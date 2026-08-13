import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import streamlit as st
from app.agents.pa_agent import ask_agent
from app.agents.self_evolve import analyze_requests_locally
from app.services.action_engine import (
    build_dashboard_summary,
    build_timeline,
    capture_inbox_entry,
    create_asset,
    create_decision,
    create_document,
    create_event,
    create_project,
    create_task,
    update_decision,
    update_task,
)
from app.services.memory_service import save_memory, get_recent_memory_text
from app.services.document_service import save_uploaded_file
from app.services.storage_service import list_records

st.set_page_config(page_title="WilliamOS", page_icon="🧠", layout="wide")

st.title("WilliamOS")
st.caption("Mini-Jarvis prototype for HouseOS, LifeOS og self-evolve")

if "messages" not in st.session_state:
    st.session_state.messages = []


def _options(records: list[dict], label_key: str) -> dict[str, str | None]:
    return {"Ingen": None, **{record[label_key]: record["id"] for record in records}}


def _show_collection(records: list[dict], columns: list[str]) -> None:
    if not records:
        st.info("Ingen registreringer ennå.")
        return
    st.dataframe([{column: record.get(column) for column in columns} for record in records], use_container_width=True)


with st.sidebar:
    st.header("Navigasjon")
    page = st.radio(
        "Velg",
        ["Dashboard", "Inbox", "Chat", "Oppgaver", "Eiendeler", "Prosjekter", "Beslutninger", "Hendelser", "Dokumenter", "Timeline", "Minne", "self-evolve"],
    )
    st.divider()
    st.caption("Byggesteiner: inbox, assets, tasks, decisions, timeline.")

if page == "Dashboard":
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
    _show_collection(dashboard["priorities"], ["title", "priority", "due_date", "status"])
    st.markdown("### Kommende hendelser")
    _show_collection(dashboard["upcoming_events"], ["title", "event_date", "event_type"])
    st.markdown("### Aktive prosjekter")
    _show_collection(dashboard["active_projects"], ["name", "status", "next_action"])
    st.markdown("### Nye dokumenter")
    _show_collection(dashboard["new_documents"], ["filename", "created_at"])
    st.markdown("### Nylig aktivitet")
    _show_collection(dashboard["recent_activity"], ["title", "event_type", "created_at"])

elif page == "Inbox":
    st.subheader("Inbox")
    with st.form("inbox_form"):
        inbox_text = st.text_area("Skriv noe du vil fange opp", placeholder="Vurderer å kjøpe Pioner 320 til 25 000")
        submitted = st.form_submit_button("Legg i inbox")
    if submitted and inbox_text.strip():
        captured = capture_inbox_entry(inbox_text.strip())
        st.success("Lagret i inbox")
        st.json(captured)
    st.markdown("### Siste inbox-signaler")
    _show_collection(list_records("inbox_items"), ["text", "status", "created_at"])

elif page == "Chat":
    st.subheader("PA-chat")

    use_documents = st.toggle("Bruk opplastede dokumenter", value=True, help="La chatten søke i dokumenter lastet opp fra alle moduler")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                with st.expander("📎 Kilder brukt", expanded=False):
                    for src in msg["sources"]:
                        st.caption(f"**{src['filename']}** (modul: {src.get('source_module') or 'ukjent'}) — score: {src['score']:.2f}")
                        if src.get("snippet"):
                            st.text(src["snippet"][:300])

    prompt = st.chat_input("Hva trenger du hjelp med?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("WilliamOS tenker..."):
                # Pass all previous turns (excluding the current prompt) as history
                # so the model remembers context across messages.
                prior_history = [
                    {"role": m["role"], "content": m.get("content") or ""}
                    for m in st.session_state.messages[:-1]
                    if m.get("role") in ("user", "assistant")
                ]
                answer, sources = ask_agent(prompt, use_documents=use_documents, history=prior_history)
            st.write(answer)
            if sources:
                with st.expander("📎 Kilder brukt", expanded=False):
                    for src in sources:
                        st.caption(f"**{src['filename']}** (modul: {src.get('source_module') or 'ukjent'}) — score: {src['score']:.2f}")
                        if src.get("snippet"):
                            st.text(src["snippet"][:300])
        st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})

elif page == "Oppgaver":
    st.subheader("Oppgaver")
    assets = list_records("assets")
    projects = list_records("projects")
    tasks = list_records("tasks")
    asset_options = _options(assets, "name")
    project_options = _options(projects, "name")
    with st.form("task_form"):
        title = st.text_input("Tittel")
        description = st.text_area("Beskrivelse")
        due_date = st.date_input("Frist", value=None)
        priority = st.slider("Prioritet", 1, 3, 2)
        asset_name = st.selectbox("Knytt til eiendel", list(asset_options.keys()))
        project_name = st.selectbox("Knytt til prosjekt", list(project_options.keys()))
        submitted = st.form_submit_button("Opprett oppgave")
    if submitted and title.strip():
        create_task(
            {
                "title": title.strip(),
                "description": description or None,
                "due_date": due_date.isoformat() if due_date else None,
                "priority": priority,
                "asset_id": asset_options[asset_name],
                "project_id": project_options[project_name],
                "status": "open",
            }
        )
        st.rerun()
    for task in tasks:
        with st.container(border=True):
            st.write(f"**{task['title']}**")
            st.caption(f"Prioritet {task.get('priority', 2)} · Status: {task.get('status', 'open')}")
            if task.get("description"):
                st.write(task["description"])
            if not task.get("completed") and st.button("Marker som fullført", key=f"complete_{task['id']}"):
                update_task(task["id"], {"completed": True, "status": "completed"})
                st.rerun()

elif page == "Eiendeler":
    st.subheader("Eiendeler")
    assets = list_records("assets")
    with st.form("asset_form"):
        name = st.text_input("Navn")
        asset_type = st.text_input("Type", placeholder="Bolig, bil, båt ...")
        status = st.selectbox("Status", ["active", "considering_purchase", "inactive"])
        estimated_value = st.number_input("Estimert verdi", min_value=0.0, value=0.0, step=1000.0)
        description = st.text_area("Beskrivelse")
        submitted = st.form_submit_button("Opprett eiendel")
    if submitted and name.strip():
        create_asset(
            {
                "name": name.strip(),
                "type": asset_type or None,
                "status": status,
                "estimated_value": estimated_value or None,
                "description": description or None,
            }
        )
        st.rerun()
    _show_collection(assets, ["name", "type", "status", "estimated_value", "created_at"])

elif page == "Prosjekter":
    st.subheader("Prosjekter")
    assets = list_records("assets")
    projects = list_records("projects")
    asset_options = _options(assets, "name")
    with st.form("project_form"):
        name = st.text_input("Prosjektnavn")
        status = st.selectbox("Status", ["active", "on_hold", "done"])
        next_action = st.text_input("Neste handling")
        notes = st.text_area("Notater")
        asset_name = st.selectbox("Knytt til eiendel", list(asset_options.keys()), key="project_asset")
        submitted = st.form_submit_button("Opprett prosjekt")
    if submitted and name.strip():
        create_project(
            {
                "name": name.strip(),
                "status": status,
                "next_action": next_action or None,
                "notes": notes or None,
                "asset_id": asset_options[asset_name],
            }
        )
        st.rerun()
    _show_collection(projects, ["name", "status", "next_action", "created_at"])

elif page == "Beslutninger":
    st.subheader("Beslutninger")
    assets = list_records("assets")
    projects = list_records("projects")
    decisions = list_records("decisions")
    asset_options = _options(assets, "name")
    project_options = _options(projects, "name")
    with st.form("decision_form"):
        title = st.text_input("Tittel")
        summary = st.text_area("Beskrivelse")
        status = st.selectbox("Status", ["open", "decided", "paused"])
        next_action = st.text_input("Neste handling")
        asset_name = st.selectbox("Knytt til eiendel", list(asset_options.keys()), key="decision_asset")
        project_name = st.selectbox("Knytt til prosjekt", list(project_options.keys()), key="decision_project")
        submitted = st.form_submit_button("Opprett beslutning")
    if submitted and title.strip():
        create_decision(
            {
                "title": title.strip(),
                "summary": summary or None,
                "status": status,
                "next_action": next_action or None,
                "asset_id": asset_options[asset_name],
                "project_id": project_options[project_name],
            }
        )
        st.rerun()
    for decision in decisions:
        with st.container(border=True):
            st.write(f"**{decision['title']}**")
            st.caption(f"Status: {decision.get('status', 'open')}")
            if decision.get("summary"):
                st.write(decision["summary"])
            if decision.get("status") != "decided" and st.button("Marker som besluttet", key=f"decide_{decision['id']}"):
                update_decision(decision["id"], {"status": "decided"})
                st.rerun()

elif page == "Hendelser":
    st.subheader("Hendelser")
    assets = list_records("assets")
    projects = list_records("projects")
    decisions = list_records("decisions")
    events = list_records("events")
    asset_options = _options(assets, "name")
    project_options = _options(projects, "name")
    decision_options = _options(decisions, "title")
    with st.form("event_form"):
        title = st.text_input("Tittel")
        event_type = st.selectbox("Type", ["general", "maintenance", "meeting", "deadline", "purchase"])
        event_date = st.date_input("Dato", value=None)
        notes = st.text_area("Notater")
        asset_name = st.selectbox("Knytt til eiendel", list(asset_options.keys()), key="event_asset")
        project_name = st.selectbox("Knytt til prosjekt", list(project_options.keys()), key="event_project")
        decision_name = st.selectbox("Knytt til beslutning", list(decision_options.keys()), key="event_decision")
        submitted = st.form_submit_button("Logg hendelse")
    if submitted and title.strip():
        create_event(
            {
                "title": title.strip(),
                "event_type": event_type,
                "event_date": event_date.isoformat() if event_date else None,
                "notes": notes or None,
                "asset_id": asset_options[asset_name],
                "project_id": project_options[project_name],
                "decision_id": decision_options[decision_name],
            }
        )
        st.rerun()
    _show_collection(events, ["title", "event_type", "event_date", "created_at"])

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
    assets = list_records("assets")
    projects = list_records("projects")
    documents = list_records("documents")
    asset_options = _options(assets, "name")
    project_options = _options(projects, "name")
    uploaded = st.file_uploader("Last opp PDF, bilde eller fil", type=None)
    asset_name = st.selectbox("Knytt til eiendel", list(asset_options.keys()), key="document_asset")
    project_name = st.selectbox("Knytt til prosjekt", list(project_options.keys()), key="document_project")
    if uploaded is not None:
        if st.button("Lagre dokument"):
            saved = save_uploaded_file(uploaded.name, uploaded.getvalue())
            create_document(
                {
                    **saved,
                    "asset_id": asset_options[asset_name],
                    "project_id": project_options[project_name],
                    "source_module": "documents",
                }
            )
            st.success("Dokument lagret lokalt")
            st.json(saved)
    st.markdown("### Dokumenter")
    _show_collection(documents, ["filename", "storage_path", "created_at"])

elif page == "Timeline":
    st.subheader("Timeline")
    timeline = build_timeline()
    _show_collection(timeline, ["title", "event_type", "event_date", "created_at", "notes"])

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
