"""Assets page — create, edit and view assets with asset-first detail."""

import streamlit as st

from app.services.action_engine import create_asset, get_asset_detail, update_asset
from app.services.storage_service import list_records
from frontend.components.record_helpers import render_collection


def _render_asset_detail(asset_id: str) -> None:
    detail = get_asset_detail(asset_id)
    if not detail:
        st.warning("Eiendel ikke funnet.")
        return

    asset = detail["asset"]
    st.markdown(f"### {asset['name']}")
    st.caption(
        f"Type: {asset.get('type') or '—'} · "
        f"Status: {asset.get('status', 'active')} · "
        f"Verdi: {asset.get('estimated_value') or '—'}"
    )
    if asset.get("description"):
        st.write(asset["description"])

    tab_tasks, tab_projects, tab_docs, tab_decisions, tab_timeline = st.tabs(
        ["Oppgaver", "Prosjekter", "Dokumenter", "Beslutninger", "Historikk"]
    )

    with tab_tasks:
        if detail["open_tasks"]:
            render_collection(detail["open_tasks"], ["title", "priority", "due_date", "status"])
        else:
            st.info("Ingen åpne oppgaver.")

    with tab_projects:
        render_collection(detail["projects"], ["name", "status", "next_action"])

    with tab_docs:
        render_collection(detail["documents"], ["filename", "created_at"])

    with tab_decisions:
        render_collection(detail["decisions"], ["title", "status", "summary"])

    with tab_timeline:
        render_collection(detail["events"], ["title", "event_type", "created_at", "notes"])


def render_assets() -> None:
    """Render the Eiendeler (Assets) page."""
    st.subheader("Eiendeler")

    assets = list_records("assets")

    with st.expander("Opprett ny eiendel", expanded=not assets):
        with st.form("asset_form"):
            name = st.text_input("Navn")
            asset_type = st.text_input("Type", placeholder="Bolig, bil, båt ...")
            status = st.selectbox("Status", ["active", "considering_purchase", "inactive"])
            estimated_value = st.number_input(
                "Estimert verdi", min_value=0.0, value=0.0, step=1000.0
            )
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

    if not assets:
        st.info("Ingen eiendeler ennå. Opprett din første over.")
        return

    asset_options = {asset["name"]: asset["id"] for asset in assets}
    selected_name = st.selectbox("Velg eiendel", list(asset_options.keys()))
    selected_id = asset_options[selected_name]

    with st.expander("Rediger eiendel"):
        current = next(a for a in assets if a["id"] == selected_id)
        with st.form(f"edit_asset_{selected_id}"):
            new_name = st.text_input("Navn", value=current.get("name", ""))
            new_type = st.text_input("Type", value=current.get("type") or "")
            new_status = st.selectbox(
                "Status",
                ["active", "considering_purchase", "inactive"],
                index=max(
                    0,
                    ["active", "considering_purchase", "inactive"].index(
                        current.get("status", "active")
                    )
                    if current.get("status", "active") in ["active", "considering_purchase", "inactive"]
                    else 0,
                ),
            )
            new_value = st.number_input(
                "Estimert verdi",
                min_value=0.0,
                value=float(current.get("estimated_value") or 0),
                step=1000.0,
            )
            new_description = st.text_area("Beskrivelse", value=current.get("description") or "")
            if st.form_submit_button("Lagre endringer"):
                update_asset(
                    selected_id,
                    {
                        "name": new_name.strip(),
                        "type": new_type or None,
                        "status": new_status,
                        "estimated_value": new_value or None,
                        "description": new_description or None,
                    },
                )
                st.rerun()

    _render_asset_detail(selected_id)

    st.markdown("### Alle eiendeler")
    render_collection(assets, ["name", "type", "status", "estimated_value", "created_at"])
