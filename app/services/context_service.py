"""Build compact context blocks injected into the PA agent system prompt."""

from __future__ import annotations

from app.services.action_engine import build_priority_engine, build_timeline
from app.services.calendar_service import list_upcoming


def _format_upcoming_events(limit: int = 5) -> str:
    try:
        upcoming = list_upcoming(days=14, limit=limit)
    except Exception:
        return ""
    if not upcoming:
        return ""
    lines = []
    for event in upcoming:
        date = str(event.get("start_at") or event.get("event_date") or "")[:16].replace("T", " ")
        title = event.get("title") or "Hendelse"
        source = event.get("source") or "internal"
        suffix = " · Google" if source == "google" else ""
        lines.append(f"- {title} ({date}){suffix}")
    return "Kommende kalender:\n" + "\n".join(lines)


def build_agent_context_blocks() -> list[str]:
    """Return short system-message blocks for situational awareness."""
    try:
        return _build_context_blocks_inner()
    except Exception:
        return []


def _build_context_blocks_inner() -> list[str]:
    blocks: list[str] = []

    focus = build_priority_engine(limit=5)
    items = focus.get("items") or []
    if items:
        lines = []
        for item in items[:5]:
            title = item.get("title") or item.get("name") or "Ukjent"
            reason = item.get("reason") or item.get("kind") or ""
            lines.append(f"- {title} ({reason})")
        blocks.append("Prioritert fokus akkurat nå:\n" + "\n".join(lines))

    schedule = _format_upcoming_events()
    if schedule:
        blocks.append(schedule)

    timeline = build_timeline(limit=5)
    if timeline:
        lines = []
        for event in timeline:
            title = event.get("title") or "Hendelse"
            event_type = event.get("event_type") or "aktivitet"
            lines.append(f"- {title} ({event_type})")
        blocks.append("Nylig aktivitet:\n" + "\n".join(lines))

    return blocks
