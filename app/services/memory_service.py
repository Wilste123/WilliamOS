"""Auto-memory from module events and manual save helpers."""

from __future__ import annotations

from app.services.storage_service import create_record, list_records

_MEMORY_EVENT_TYPES = frozenset(
    {
        "asset_created",
        "asset_updated",
        "task_created",
        "task_updated",
        "goal_created",
        "goal_updated",
        "project_created",
        "project_updated",
        "document_created",
        "inbox_suggestion_applied",
        "health_metric_created",
        "finance_account_created",
        "finance_account_updated",
        "decision_created",
    }
)

_COMPLETION_HINTS = ("fullført", "completed", "ferdig", "done")


def _should_skip_duplicate(value: str, limit: int = 50) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return True
    recent = list_records("memory_items")[:limit]
    return any(str(row.get("value", "")).strip().lower() == normalized for row in recent)


def append_memory_from_event(
    event_type: str,
    title: str,
    notes: str | None = None,
) -> dict | None:
    """Create a memory item from selected system events (rule-based v1)."""
    if event_type not in _MEMORY_EVENT_TYPES:
        return None

    if event_type == "task_updated":
        combined = f"{title} {notes or ''}".lower()
        if not any(hint in combined for hint in _COMPLETION_HINTS):
            if "completed" not in combined and "status" not in combined:
                return None

    if event_type == "goal_updated":
        combined = f"{title} {notes or ''}".lower()
        if "completed" not in combined and "fullført" not in combined:
            return None

    if event_type in {"asset_updated", "project_updated", "finance_account_updated"}:
        return None

    parts = [title.strip()]
    if notes and notes.strip():
        parts.append(notes.strip())
    value = " — ".join(parts)
    if _should_skip_duplicate(value):
        return None

    category = _category_for_event(event_type)
    key = _key_for_event(event_type, title)
    return save_memory(value, key=key, category=category, source=event_type)


def _category_for_event(event_type: str) -> str:
    if event_type.startswith("asset"):
        return "eiendel"
    if event_type.startswith("task"):
        return "oppgave"
    if event_type.startswith("goal"):
        return "mål"
    if event_type.startswith("project"):
        return "prosjekt"
    if event_type.startswith("document"):
        return "dokument"
    if event_type.startswith("health"):
        return "helse"
    if event_type.startswith("finance"):
        return "økonomi"
    if event_type.startswith("decision"):
        return "beslutning"
    if event_type.startswith("inbox"):
        return "inbox"
    return "system"


def _key_for_event(event_type: str, title: str) -> str:
    slug = title.lower().replace(":", "").strip()[:40]
    return f"{event_type}:{slug}"


def get_recent_memory_text(limit: int = 20) -> str:
    """Fetch recent memory items from Supabase."""
    rows = list_records("memory_items")[:limit]
    if not rows:
        return "Ingen lagret minne ennå."
    return "\n".join(f"- {r['value']}" for r in rows)


def save_memory(
    value: str,
    key: str | None = None,
    category: str | None = None,
    visibility: str = "private",
    source: str | None = None,
) -> dict:
    """Persist a memory item to Supabase."""
    payload: dict = {"value": value, "key": key, "category": category, "visibility": visibility}
    if source:
        payload["source"] = source
    record = create_record("memory_items", payload)
    return {"saved": True, "data": record}
