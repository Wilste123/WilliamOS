"""Shared UI helper functions used across multiple Streamlit page modules.

These helpers are Streamlit-aware (they call ``st.*``), so they live in the
UI layer.  They operate on generic list-of-dict payloads returned by the
service layer, keeping the actual business/data logic out of the UI.
"""

import streamlit as st


def build_record_options(records: list[dict], label_key: str) -> dict[str, str | None]:
    """Build a ``{label: id}`` mapping suitable for ``st.selectbox``.

    The first entry is always ``{"Ingen": None}`` so the user can leave a
    relation field empty.

    Args:
        records: list of dicts, each containing at minimum ``id`` and
            ``label_key``.
        label_key: the dict key whose value is used as the human-readable
            label (e.g. ``"name"`` or ``"title"``).

    Returns:
        Ordered dict with ``"Ingen"`` first, then one entry per record.
    """
    return {"Ingen": None, **{record[label_key]: record["id"] for record in records}}


def render_collection(records: list[dict], columns: list[str]) -> None:
    """Render a list of records as a Streamlit dataframe.

    Displays an info message when *records* is empty so the user knows no
    data exists yet, rather than showing a blank table.

    Args:
        records: list of dicts to display.
        columns: which keys to show as columns (in order).
    """
    if not records:
        st.info("Ingen registreringer ennå.")
        return
    st.dataframe(
        [{col: record.get(col) for col in columns} for record in records],
        use_container_width=True,
    )
