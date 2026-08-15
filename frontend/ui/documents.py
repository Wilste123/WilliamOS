"""Documents page — upload files and attach them to assets/projects."""

import streamlit as st

from app.services.action_engine import save_document
from app.services.storage_service import list_records
from frontend.components.record_helpers import build_record_options, render_collection


def render_documents() -> None:
    """Render the Dokumenter (Documents) page."""
    st.subheader("Dokumenter")

    assets = list_records("assets")
    projects = list_records("projects")
    documents = list_records("documents")
    asset_options = build_record_options(assets, "name")
    project_options = build_record_options(projects, "name")

    uploaded = st.file_uploader("Last opp PDF, bilde eller fil", type=None)
    asset_name = st.selectbox(
        "Knytt til eiendel", list(asset_options.keys()), key="document_asset"
    )
    project_name = st.selectbox(
        "Knytt til prosjekt", list(project_options.keys()), key="document_project"
    )

    if uploaded is not None:
        if st.button("Lagre dokument"):
            save_document(
                uploaded.name,
                uploaded.getvalue(),
                asset_id=asset_options[asset_name],
                project_id=project_options[project_name],
            )
            st.success("Dokument lagret i Supabase")
            st.rerun()

    st.markdown("### Dokumenter")
    render_collection(documents, ["filename", "storage_path", "created_at"])
