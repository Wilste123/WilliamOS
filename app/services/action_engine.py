import re
from datetime import datetime, timezone

from app.services.storage_service import append_event, create_record, list_records, update_record


def create_asset(payload: dict) -> dict:
    asset = create_record("assets", payload)
    append_event(
        title=f"Eiendel opprettet: {asset['name']}",
        event_type="asset_created",
        notes=asset.get("description"),
        asset_id=asset["id"],
    )
    return asset


def update_asset(asset_id: str, updates: dict) -> dict | None:
    asset = update_record("assets", asset_id, updates)
    if asset:
        append_event(
            title=f"Eiendel oppdatert: {asset['name']}",
            event_type="asset_updated",
            asset_id=asset["id"],
        )
    return asset


def create_task(payload: dict) -> dict:
    task = create_record("tasks", {**payload, "completed": payload.get("completed", False)})
    append_event(
        title=f"Oppgave opprettet: {task['title']}",
        event_type="task_created",
        notes=task.get("description"),
        asset_id=task.get("asset_id"),
        project_id=task.get("project_id"),
    )
    return task


def update_task(task_id: str, updates: dict) -> dict | None:
    task = update_record("tasks", task_id, updates)
    if task:
        append_event(
            title=f"Oppgave oppdatert: {task['title']}",
            event_type="task_updated",
            notes=f"Status: {task.get('status')}, fullført: {task.get('completed')}",
            asset_id=task.get("asset_id"),
            project_id=task.get("project_id"),
        )
    return task


def create_project(payload: dict) -> dict:
    project = create_record("projects", payload)
    append_event(
        title=f"Prosjekt opprettet: {project['name']}",
        event_type="project_created",
        notes=project.get("next_action"),
        asset_id=project.get("asset_id"),
        project_id=project["id"],
    )
    return project


def update_project(project_id: str, updates: dict) -> dict | None:
    project = update_record("projects", project_id, updates)
    if project:
        append_event(
            title=f"Prosjekt oppdatert: {project['name']}",
            event_type="project_updated",
            project_id=project["id"],
        )
    return project


def create_document(payload: dict) -> dict:
    document = create_record("documents", payload)
    append_event(
        title=f"Dokument lagret: {document['filename']}",
        event_type="document_created",
        asset_id=document.get("asset_id"),
        project_id=document.get("project_id"),
    )
    return document


def create_decision(payload: dict) -> dict:
    if payload.get("status") == "decided" and not payload.get("decided_at"):
        payload["decided_at"] = datetime.now(timezone.utc).isoformat()
    decision = create_record("decisions", payload)
    append_event(
        title=f"Beslutning registrert: {decision['title']}",
        event_type="decision_created",
        notes=decision.get("summary"),
        asset_id=decision.get("asset_id"),
        project_id=decision.get("project_id"),
        decision_id=decision["id"],
    )
    return decision


def update_decision(decision_id: str, updates: dict) -> dict | None:
    if updates.get("status") == "decided" and not updates.get("decided_at"):
        updates["decided_at"] = datetime.now(timezone.utc).isoformat()
    decision = update_record("decisions", decision_id, updates)
    if decision:
        append_event(
            title=f"Beslutning oppdatert: {decision['title']}",
            event_type="decision_updated",
            decision_id=decision["id"],
            asset_id=decision.get("asset_id"),
            project_id=decision.get("project_id"),
        )
    return decision


def create_event(payload: dict) -> dict:
    return create_record("events", payload)


def capture_inbox_entry(text: str) -> dict:
    amount_match = re.search(
        r"\btil\s+(\d[\d\s]*\d|\d)\s*(?:kr|nok|,-)?(?:\b|$)",
        text,
        flags=re.IGNORECASE,
    )
    amount = amount_match.group(1).replace(" ", "") if amount_match else None
    lowered = text.lower()
    suggestions = []

    if "kjøp" in lowered or "kjøpe" in lowered:
        suggestions.append(
            {
                "object_type": "asset",
                "fields": {
                    "name": re.split(r"\btil\b", text, flags=re.IGNORECASE)[0].strip(),
                    "status": "considering_purchase",
                    "estimated_value": float(amount) if amount else None,
                },
            }
        )
        suggestions.append(
            {
                "object_type": "decision",
                "fields": {
                    "title": f"Vurdere: {text[:60]}",
                    "summary": text,
                    "status": "open",
                },
            }
        )

    if any(keyword in lowered for keyword in ["må", "skal", "trenger", "oppgave"]):
        suggestions.append(
            {
                "object_type": "task",
                "fields": {
                    "title": text[:80],
                    "priority": 2,
                    "status": "open",
                },
            }
        )

    inbox_item = create_record(
        "inbox_items",
        {
            "text": text,
            "suggestions": suggestions,
            "status": "captured",
        },
    )
    append_event(
        title=f"Innboksfangst: {text[:60]}",
        event_type="inbox_captured",
        notes=f"{len(suggestions)} forslag generert",
    )
    return inbox_item


def build_dashboard_summary() -> dict:
    tasks = list_records("tasks")
    projects = list_records("projects")
    assets = list_records("assets")
    documents = list_records("documents")
    decisions = list_records("decisions")
    events = list_records("events")

    open_tasks = [task for task in tasks if not task.get("completed")]
    priorities = sorted(
        open_tasks,
        key=lambda task: (
            -(task.get("priority") or 0),
            task.get("due_date") or "9999-12-31T23:59:59",
        ),
    )[:5]
    upcoming_events = sorted(
        [event for event in events if event.get("event_date")],
        key=lambda event: event.get("event_date") or "9999-12-31T23:59:59",
    )[:5]
    return {
        "metrics": {
            "assets": len(assets),
            "open_tasks": len(open_tasks),
            "projects": len([project for project in projects if project.get("status") == "active"]),
            "documents": len(documents),
            "open_decisions": len([decision for decision in decisions if decision.get("status") != "decided"]),
        },
        "priorities": priorities,
        "upcoming_events": upcoming_events,
        "active_projects": [project for project in projects if project.get("status") == "active"][:5],
        "new_documents": documents[:5],
        "recent_activity": events[:8],
    }


def build_timeline(limit: int = 50) -> list[dict]:
    events = list_records("events")
    return sorted(
        events,
        key=lambda event: event.get("event_date") or event.get("created_at", ""),
        reverse=True,
    )[:limit]
