"""Mission planner — break a natural-language goal into executable proposals."""

from __future__ import annotations

import json
import re

from app.services.chat_actions import build_proposal

ALLOWED_MISSION_TOOLS = frozenset(
    {
        "create_task",
        "create_decision",
        "create_project",
        "create_asset",
        "capture_inbox",
        "save_memory",
        "create_calendar_event",
        "create_goal",
    }
)


def _steps_for_goal(goal: str) -> list[tuple[str, dict]]:
    lowered = goal.lower()
    steps: list[tuple[str, dict]] = []

    if any(word in lowered for word in ("hytte", "cabin", "ferie")):
        steps.append(
            (
                "create_task",
                {
                    "title": "Lag pakkeliste for hyttetur",
                    "priority": 2,
                    "status": "open",
                },
            )
        )
        steps.append(
            (
                "create_task",
                {
                    "title": "Sjekk strøm og vann før avreise",
                    "priority": 3,
                    "status": "open",
                },
            )
        )

    if any(word in lowered for word in ("forsikring", "insurance")):
        steps.append(
            (
                "create_decision",
                {
                    "title": f"Vurder forsikring: {goal[:80]}",
                    "status": "open",
                },
            )
        )
        steps.append(
            (
                "create_task",
                {
                    "title": "Sammenlign forsikringstilbud",
                    "priority": 3,
                    "status": "open",
                },
            )
        )

    if "møte" in lowered or "kalender" in lowered:
        steps.append(
            (
                "create_task",
                {
                    "title": f"Forbered: {goal[:80]}",
                    "priority": 2,
                    "status": "open",
                },
            )
        )

    if not steps:
        steps.append(
            (
                "create_task",
                {
                    "title": goal[:120] or "Nytt oppdrag",
                    "priority": 2,
                    "status": "open",
                },
            )
        )
        steps.append(
            (
                "capture_inbox",
                {"text": f"Oppdrag: {goal}"},
            )
        )

    return steps


def _plan_mission_with_llm(goal: str) -> list[tuple[str, dict]] | None:
    from app.services.openai_service import chat_completion

    prompt = f"""Du er en oppdragsplanlegger for WilliamOS.
Bryt målet ned i 2-6 konkrete steg som JSON-array.
Hvert steg: {{"tool": "<tool_name>", "args": {{...}}}}
Tillatte tools: {", ".join(sorted(ALLOWED_MISSION_TOOLS))}
Svar KUN med JSON-array, ingen markdown.

Mål: {goal}
"""
    raw = chat_completion(
        [
            {"role": "system", "content": "Returner kun gyldig JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    if not raw or raw.startswith("OpenAI"):
        return None

    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, list):
        return None

    steps: list[tuple[str, dict]] = []
    for entry in payload[:8]:
        if not isinstance(entry, dict):
            continue
        tool = str(entry.get("tool") or "")
        args = entry.get("args") if isinstance(entry.get("args"), dict) else {}
        if tool not in ALLOWED_MISSION_TOOLS:
            continue
        steps.append((tool, args))
    return steps or None


def plan_mission(goal: str) -> dict:
    """Return a mission plan as a list of action proposals (not executed)."""
    cleaned = re.sub(r"^(oppdrag|mission)\s*[:\-]\s*", "", goal.strip(), flags=re.IGNORECASE)
    if not cleaned:
        cleaned = goal.strip()

    steps = _plan_mission_with_llm(cleaned)
    planner = "llm" if steps else "rules"
    if not steps:
        steps = _steps_for_goal(cleaned)
    proposals = [build_proposal(tool, args) for tool, args in steps]

    lines = [f"📋 Oppdragsplan: {cleaned}", ""]
    for index, proposal in enumerate(proposals, start=1):
        lines.append(f"{index}. {proposal['label']}: {proposal['title']}")

    return {
        "goal": cleaned,
        "summary": "\n".join(lines),
        "steps": [{"tool": p["tool"], "title": p["title"]} for p in proposals],
        "proposals": proposals,
        "planner": planner,
    }
