"""Visibility selector for private vs household-shared records."""

import streamlit as st


def visibility_selectbox(*, key: str, default: str = "household") -> str:
    """Return ``household`` or ``private`` based on user choice."""
    options = ["Delt med husholdning", "Privat"]
    index = 0 if default == "household" else 1
    choice = st.radio("Synlighet", options, index=index, horizontal=True, key=key)
    return "household" if choice == "Delt med husholdning" else "private"


def visibility_badge(record: dict) -> str:
    if record.get("visibility") == "private":
        return "Privat"
    return "Delt"
