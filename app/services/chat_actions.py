"""Build chat action cards from tool results and assistant proposals."""

from __future__ import annotations

import re

_TOOL_ACTION_MAP: dict[str, tuple[str, str]] = {
    "create_task": ("create_task", "Opprett oppgave"),
    "create_asset": ("create_asset", "Opprett eiendel"),
    "create_project": ("create_project", "Opprett prosjekt"),
    "create_decision": ("create_decision", "Opprett beslutning"),
    "update_task": ("update_task", "Oppdater oppgave"),
    "update_asset": ("update_asset", "Oppdater eiendel"),
}


def tool_result_to_action(func_name: str, args: dict, result: object) -> dict | None:
    if not isinstance(result, dict) or result.get("error"):
        return None
    mapping = _TOOL_ACTION_MAP.get(func_name)
    if not mapping:
        return None
    action_type, label = mapping
    title = (
        result.get("title")
        or result.get("name")
        or args.get("title")
        or args.get("name")
        or label
    )
    return {
        "id": f"done-{func_name}-{result.get('id', title)}",
        "type": action_type,
        "label": label,
        "title": str(title),
        "status": "completed",
        "payload": args,
        "result_id": result.get("id"),
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

    for action_type, label, pattern in patterns:
        match = pattern.search(assistant_text)
        if not match:
            continue
        title = match.group(1).strip(" \"'[]")
        if len(title) < 3:
            continue
        proposals.append(
            {
                "id": f"proposed-{action_type}-{len(proposals)}",
                "type": action_type,
                "label": label,
                "title": title,
                "status": "proposed",
                "payload": {"title": title, "priority": 2, "status": "open"},
            }
        )
    return proposals


def merge_chat_actions(completed: list[dict], assistant_text: str) -> list[dict]:
    actions = list(completed)
    if completed:
        return actions
    return extract_proposed_actions(assistant_text)
