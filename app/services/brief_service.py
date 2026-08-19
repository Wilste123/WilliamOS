"""Proactive daily brief with executable action proposals for Home."""

from __future__ import annotations

from datetime import date, timedelta

from app.services.action_engine import build_priority_engine, build_weekly_brief
from app.services.chat_actions import build_proposal
from app.services.profile_service import DEFAULT_PREFERENCES, get_user_profile
from app.services.storage_service import list_records


def _inbox_proposals(limit: int = 4) -> list[dict]:
    proposals: list[dict] = []
    try:
        inbox_items = list_records("inbox_items")
    except Exception:
        return proposals

    for item in inbox_items:
        if item.get("status") in ("processed", "dismissed"):
            continue
        suggestions = item.get("suggestions") or []
        if not suggestions:
            continue
        inbox_id = str(item.get("id") or "")
        text = str(item.get("text") or item.get("subject") or "Inbox")[:60]
        for index, suggestion in enumerate(suggestions[:2]):
            object_type = suggestion.get("object_type") or "element"
            fields = suggestion.get("fields") or {}
            title = (
                fields.get("title")
                or fields.get("name")
                or f"{object_type} fra inbox"
            )
            proposals.append(
                {
                    **build_proposal(
                        "apply_inbox_suggestion",
                        {"inbox_id": inbox_id, "suggestion_index": index},
                    ),
                    "title": f"{title} ({text})",
                    "source": "inbox",
                }
            )
            if len(proposals) >= limit:
                return proposals
    return proposals


def _overdue_task_proposals(engine: dict, limit: int = 3) -> list[dict]:
    proposals: list[dict] = []
    for item in engine.get("items") or []:
        if item.get("source_type") != "task":
            continue
        if not item.get("meta", {}).get("overdue"):
            continue
        record = item.get("record") or {}
        task_id = record.get("id")
        if not task_id:
            continue
        proposals.append(
            {
                **build_proposal(
                    "update_task",
                    {"task_id": str(task_id), "status": "in_progress"},
                ),
                "title": f"Start: {item.get('title')}",
                "source": "overdue_task",
            }
        )
        if len(proposals) >= limit:
            break
    return proposals


def _calendar_prep_proposals(limit: int = 2) -> list[dict]:
    from app.services.calendar_service import list_upcoming

    proposals: list[dict] = []
    try:
        events = list_upcoming(days=3, limit=10)
    except Exception:
        return proposals

    for event in events:
        title = str(event.get("title") or "Avtale")
        start = str(event.get("start_at") or "")[:10]
        if not start:
            continue
        prep_date = (date.fromisoformat(start) - timedelta(days=1)).isoformat()
        proposals.append(
            {
                **build_proposal(
                    "create_task",
                    {
                        "title": f"Forbered: {title}",
                        "due_date": prep_date,
                        "priority": 2,
                        "status": "open",
                    },
                ),
                "title": f"Forbered: {title}",
                "source": "calendar",
            }
        )
        if len(proposals) >= limit:
            break
    return proposals


def build_daily_brief() -> dict:
    """Return headline, summary, and actionable proposals for the Home screen."""
    engine = build_priority_engine(limit=8)
    weekly = build_weekly_brief()
    try:
        prefs = get_user_profile().get("preferences") or {}
    except Exception:
        prefs = dict(DEFAULT_PREFERENCES)
    automation = bool(prefs.get("inbox_automation", True))

    proposals: list[dict] = []
    proposals.extend(_overdue_task_proposals(engine, limit=3))

    if automation:
        proposals.extend(_inbox_proposals(limit=4))
        proposals.extend(_calendar_prep_proposals(limit=2))

    # De-dupe by id
    seen: set[str] = set()
    unique: list[dict] = []
    for proposal in proposals:
        pid = str(proposal.get("id") or "")
        if pid in seen:
            continue
        seen.add(pid)
        unique.append(proposal)

    top = (engine.get("items") or [])[:3]
    if top:
        headline = f"{len(unique)} forslag · {top[0].get('title', 'Dagen din')}"
    elif unique:
        headline = f"{len(unique)} forslag venter på deg"
    else:
        headline = "Alt i orden akkurat nå"

    return {
        "headline": headline,
        "summary": weekly.get("summary_text", "").split("\n\n")[0],
        "proposal_count": len(unique),
        "proposals": unique[:8],
        "focus_items": engine.get("items") or [],
    }
