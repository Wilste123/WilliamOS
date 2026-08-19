"""Build chat action cards and proposal pipeline for the PA agent."""

from __future__ import annotations

import hashlib
import json
import re

from app.services.action_executor import execute_chat_action

# Mutating tools that require user confirmation before execution.
PROPOSE_TOOLS: frozenset[str] = frozenset(
    {
        "create_asset",
        "update_asset",
        "delete_asset",
        "create_task",
        "update_task",
        "delete_task",
        "create_project",
        "update_project",
        "delete_project",
        "create_decision",
        "update_decision",
        "delete_decision",
        "create_goal",
        "update_goal",
        "create_document",
        "create_calendar_event",
        "update_calendar_event",
        "delete_calendar_event",
        "apply_inbox_suggestion",
    }
)

_TOOL_ACTION_MAP: dict[str, tuple[str, str]] = {
    "create_task": ("create_task", "Opprett oppgave"),
    "create_asset": ("create_asset", "Opprett eiendel"),
    "create_project": ("create_project", "Opprett prosjekt"),
    "create_decision": ("create_decision", "Opprett beslutning"),
    "create_goal": ("create_goal", "Opprett mål"),
    "update_task": ("update_task", "Oppdater oppgave"),
    "update_asset": ("update_asset", "Oppdater eiendel"),
    "update_project": ("update_project", "Oppdater prosjekt"),
    "update_decision": ("update_decision", "Oppdater beslutning"),
    "update_goal": ("update_goal", "Oppdater mål"),
    "delete_task": ("delete_task", "Slett oppgave"),
    "delete_asset": ("delete_asset", "Slett eiendel"),
    "delete_project": ("delete_project", "Slett prosjekt"),
    "delete_decision": ("delete_decision", "Slett beslutning"),
    "complete_task": ("complete_task", "Fullfør oppgave"),
    "capture_inbox": ("capture_inbox", "Fang i inbox"),
    "save_memory": ("save_memory", "Lagre minne"),
    "create_calendar_event": ("create_calendar_event", "Opprett kalenderavtale"),
    "update_calendar_event": ("update_calendar_event", "Oppdater kalenderavtale"),
    "delete_calendar_event": ("delete_calendar_event", "Slett kalenderavtale"),
    "apply_inbox_suggestion": ("apply_inbox_suggestion", "Bruk inbox-forslag"),
}


def _proposal_id(func_name: str, args: dict) -> str:
    digest = hashlib.md5(
        f"{func_name}:{json.dumps(args, sort_keys=True, default=str)}".encode()
    ).hexdigest()[:10]
    return f"proposed-{func_name}-{digest}"


def _action_title(func_name: str, args: dict, label: str) -> str:
    return str(
        args.get("title")
        or args.get("name")
        or args.get("value")
        or label
    )


def build_proposal(func_name: str, args: dict) -> dict:
    mapping = _TOOL_ACTION_MAP.get(func_name)
    if not mapping:
        action_type, label = func_name, func_name.replace("_", " ").title()
    else:
        action_type, label = mapping
    title = _action_title(func_name, args, label)
    return {
        "id": _proposal_id(func_name, args),
        "type": action_type,
        "tool": func_name,
        "label": label,
        "title": title,
        "status": "proposed",
        "payload": args,
    }


def tool_result_to_action(func_name: str, args: dict, result: object) -> dict | None:
    if not isinstance(result, dict) or result.get("error"):
        return None
    if result.get("status") == "proposed":
        return None
    mapping = _TOOL_ACTION_MAP.get(func_name)
    if not mapping:
        return None
    action_type, label = mapping
    title = _action_title(func_name, args, label)
    if result.get("deleted"):
        title = f"Slettet: {title}"
    return {
        "id": f"done-{func_name}-{result.get('id', title)}",
        "type": action_type,
        "tool": func_name,
        "label": label,
        "title": title,
        "status": "completed",
        "payload": args,
        "result_id": result.get("id"),
    }


def execute_and_finalize(action: dict) -> dict:
    """Execute a proposed action and return updated action card + result."""
    tool = str(action.get("tool") or action.get("type") or "")
    payload = action.get("payload") or {}
    result = execute_chat_action(action)
    if isinstance(result, dict) and result.get("error"):
        return {"action": action, "result": result, "ok": False}
    finalized = tool_result_to_action(tool, payload, result)
    if finalized:
        return {"action": finalized, "result": result, "ok": True}
    return {
        "action": {**action, "status": "completed"},
        "result": result,
        "ok": True,
    }


def extract_proposed_actions(assistant_text: str) -> list[dict]:
    """Detect actionable proposals in assistant prose when no tool ran."""
    if not assistant_text:
        return []

    proposals: list[dict] = []
    patterns = [
        (
            "create_task",
            "Opprett oppgave",
            re.compile(
                r"(?:burde|bør|foreslår|anbefaler).*?(?:oppgave|task)[:\s]+(.+?)(?:\.|$)",
                re.IGNORECASE,
            ),
        ),
        (
            "create_task",
            "Opprett oppgave",
            re.compile(r"\[(?:create task|opprett oppgave)\][:\s]*(.+?)(?:\.|$)", re.IGNORECASE),
        ),
    ]

    for func_name, label, pattern in patterns:
        match = pattern.search(assistant_text)
        if not match:
            continue
        title = match.group(1).strip(" \"'[]")
        if len(title) < 3:
            continue
        proposals.append(
            build_proposal(
                func_name,
                {"title": title, "priority": 2, "status": "open"},
            )
        )
    return proposals


def merge_chat_actions(actions: list[dict], assistant_text: str) -> list[dict]:
    if actions:
        return actions
    return extract_proposed_actions(assistant_text)
