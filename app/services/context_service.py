"""Build compact context blocks injected into the PA agent system prompt."""

from __future__ import annotations

from app.services.action_engine import build_priority_engine, build_timeline, get_asset_detail
from app.services.calendar_service import list_upcoming
from app.services.storage_service import list_records


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


def _build_entity_graph_block() -> str:
    """Summarize top-priority entities with related tasks, docs, and events."""
    try:
        engine = build_priority_engine(limit=5)
    except Exception:
        return ""

    asset_ids: list[str] = []
    for item in engine.get("items") or []:
        record = item.get("record") or {}
        asset_id = record.get("asset_id") or item.get("asset_id")
        if asset_id and str(asset_id) not in asset_ids:
            asset_ids.append(str(asset_id))
        if len(asset_ids) >= 2:
            break

    if not asset_ids:
        return ""

    lines = ["Relatert livskontekst (entity graph):"]
    for asset_id in asset_ids:
        detail = get_asset_detail(asset_id)
        if not detail:
            continue
        asset = detail.get("asset") or {}
        name = asset.get("name") or "Eiendel"
        open_tasks = detail.get("open_tasks") or []
        documents = detail.get("documents") or []
        lines.append(f"- {name}: {len(open_tasks)} åpne oppgaver, {len(documents)} dokumenter")
        for task in open_tasks[:2]:
            lines.append(f"  · oppgave: {task.get('title')}")
        for doc in documents[:2]:
            lines.append(f"  · dokument: {doc.get('filename')}")

    try:
        goals = [g for g in list_records("goals") if g.get("status") == "active"][:3]
        if goals:
            lines.append("Aktive mål:")
            for goal in goals:
                lines.append(f"- {goal.get('title')}")
    except Exception:
        pass

    return "\n".join(lines) if len(lines) > 1 else ""


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

    entity_graph = _build_entity_graph_block()
    if entity_graph:
        blocks.append(entity_graph)

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
