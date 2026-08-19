"""Execute chat action proposals — single write path for UI and API."""

from __future__ import annotations

from app.services.action_engine import (
    apply_inbox_suggestion,
    create_asset,
    create_decision,
    create_document,
    create_goal,
    create_project,
    create_task,
    update_asset,
    update_decision,
    update_goal,
    update_project,
    update_task,
)
from app.services.calendar_service import (
    create_calendar_event,
    delete_calendar_event,
    update_calendar_event,
)
from app.services.memory_service import save_memory
from app.services.storage_service import delete_record


def execute_chat_action(action: dict) -> dict:
    """Run one proposed/completed action card. Returns created/updated record or error dict."""
    tool = str(action.get("tool") or action.get("type") or "")
    payload = dict(action.get("payload") or {})
    clean = {k: v for k, v in payload.items() if v is not None}

    try:
        if tool == "create_task":
            body = {"priority": 2, "status": "open", **clean}
            return create_task(body)
        if tool == "update_task":
            task_id = clean.pop("task_id", None)
            if not task_id:
                return {"error": "task_id mangler"}
            return update_task(str(task_id), clean) or {"error": "Oppgave ikke funnet"}
        if tool == "complete_task":
            task_id = clean.get("task_id")
            if not task_id:
                return {"error": "task_id mangler"}
            return (
                update_task(str(task_id), {"status": "completed", "completed": True})
                or {"error": "Oppgave ikke funnet"}
            )
        if tool == "delete_task":
            task_id = clean.get("task_id")
            if not task_id:
                return {"error": "task_id mangler"}
            ok = delete_record("tasks", str(task_id))
            return {"deleted": ok, "id": task_id} if ok else {"error": "Oppgave ikke funnet"}
        if tool == "create_asset":
            return create_asset({"status": "active", **clean})
        if tool == "update_asset":
            asset_id = clean.pop("asset_id", None)
            if not asset_id:
                return {"error": "asset_id mangler"}
            return update_asset(str(asset_id), clean) or {"error": "Eiendel ikke funnet"}
        if tool == "delete_asset":
            asset_id = clean.get("asset_id")
            if not asset_id:
                return {"error": "asset_id mangler"}
            ok = delete_record("assets", str(asset_id))
            return {"deleted": ok, "id": asset_id} if ok else {"error": "Eiendel ikke funnet"}
        if tool == "create_project":
            return create_project({"status": "active", **clean})
        if tool == "update_project":
            project_id = clean.pop("project_id", None)
            if not project_id:
                return {"error": "project_id mangler"}
            return update_project(str(project_id), clean) or {"error": "Prosjekt ikke funnet"}
        if tool == "delete_project":
            project_id = clean.get("project_id")
            if not project_id:
                return {"error": "project_id mangler"}
            ok = delete_record("projects", str(project_id))
            return {"deleted": ok, "id": project_id} if ok else {"error": "Prosjekt ikke funnet"}
        if tool == "create_decision":
            return create_decision({"status": "open", **clean})
        if tool == "update_decision":
            decision_id = clean.pop("decision_id", None)
            if not decision_id:
                return {"error": "decision_id mangler"}
            return update_decision(str(decision_id), clean) or {"error": "Beslutning ikke funnet"}
        if tool == "delete_decision":
            decision_id = clean.get("decision_id")
            if not decision_id:
                return {"error": "decision_id mangler"}
            ok = delete_record("decisions", str(decision_id))
            return {"deleted": ok, "id": decision_id} if ok else {"error": "Beslutning ikke funnet"}
        if tool == "create_goal":
            return create_goal(clean)
        if tool == "update_goal":
            goal_id = clean.pop("goal_id", None)
            if not goal_id:
                return {"error": "goal_id mangler"}
            return update_goal(str(goal_id), clean) or {"error": "Mål ikke funnet"}
        if tool == "create_document":
            return create_document({"source_module": "chat", **clean})
        if tool == "save_memory":
            value = clean.get("value", "").strip()
            if not value:
                return {"error": "Tomt minne"}
            return save_memory(value, category=clean.get("category"), source="chat")
        if tool == "capture_inbox":
            from app.services.action_engine import capture_inbox_entry

            text = clean.get("text", "").strip()
            if not text:
                return {"error": "Tom inbox-tekst"}
            return capture_inbox_entry(text)
        if tool == "apply_inbox_suggestion":
            inbox_id = clean.get("inbox_id")
            index = clean.get("suggestion_index")
            if inbox_id is None or index is None:
                return {"error": "inbox_id og suggestion_index kreves"}
            return apply_inbox_suggestion(str(inbox_id), int(index))
        if tool == "create_calendar_event":
            sync_google = clean.pop("sync_google", True)
            return create_calendar_event(clean, sync_google=bool(sync_google))
        if tool == "update_calendar_event":
            event_id = clean.pop("event_id", None)
            if not event_id:
                return {"error": "event_id mangler"}
            sync_google = clean.pop("sync_google", True)
            return (
                update_calendar_event(str(event_id), clean, sync_google=bool(sync_google))
                or {"error": "Hendelse ikke funnet"}
            )
        if tool == "delete_calendar_event":
            event_id = clean.get("event_id")
            if not event_id:
                return {"error": "event_id mangler"}
            ok = delete_calendar_event(str(event_id))
            return {"deleted": ok, "id": event_id} if ok else {"error": "Hendelse ikke funnet"}
        return {"error": f"Ukjent handling: {tool}"}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
