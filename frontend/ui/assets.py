"""Assets page — create and view assets (properties, vehicles, equipment, etc.)."""

import streamlit as st

from app.services.action_engine import create_asset
from app.services.storage_service import list_records
from frontend.components.record_helpers import render_collection


def render_assets() -> None:
    """Render the Eiendeler (Assets) page."""
    st.subheader("Eiendeler")

    assets = list_records("assets")

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

    render_collection(assets, ["name", "type", "status", "estimated_value", "created_at"])
