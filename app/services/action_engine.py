import re
from datetime import datetime, timezone

from app.services.storage_service import append_event, create_record, get_record, list_records, update_record


def create_asset(payload: dict) -> dict:
    asset = create_record("assets", payload)
    append_event(
        title=f"Eiendel opprettet: {asset['name']}",
        event_type="asset_created",
        notes=asset.get("description"),
        asset_id=asset["id"],
        visibility=asset.get("visibility"),
    )
    return asset


def update_asset(asset_id: str, updates: dict) -> dict | None:
    asset = update_record("assets", asset_id, updates)
    if asset:
        append_event(
            title=f"Eiendel oppdatert: {asset['name']}",
            event_type="asset_updated",
            asset_id=asset["id"],
            visibility=asset.get("visibility"),
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
        visibility=task.get("visibility"),
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
            visibility=task.get("visibility"),
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
        visibility=project.get("visibility"),
    )
    return project


def update_project(project_id: str, updates: dict) -> dict | None:
    project = update_record("projects", project_id, updates)
    if project:
        append_event(
            title=f"Prosjekt oppdatert: {project['name']}",
            event_type="project_updated",
            project_id=project["id"],
            visibility=project.get("visibility"),
        )
    return project


def create_document(payload: dict) -> dict:
    document = create_record("documents", payload)
    append_event(
        title=f"Dokument lagret: {document['filename']}",
        event_type="document_created",
        asset_id=document.get("asset_id"),
        project_id=document.get("project_id"),
        visibility=document.get("visibility"),
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
        visibility=decision.get("visibility"),
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
            visibility=decision.get("visibility"),
        )
    return decision


def complete_task(task_id: str) -> dict | None:
    """Mark a task as completed.

    Encapsulates the business decision of which fields to set when a task is
    completed so that the UI only needs to pass the task id.
    """
    return update_task(task_id, {"completed": True, "status": "completed"})


def finalize_decision(decision_id: str) -> dict | None:
    """Mark a decision as decided.

    Encapsulates the business decision of which status value to use so that
    the UI does not need to know the internal status string.
    """
    return update_decision(decision_id, {"status": "decided"})


def save_document(
    filename: str,
    file_bytes: bytes,
    *,
    asset_id: str | None = None,
    project_id: str | None = None,
    source_module: str = "documents",
    visibility: str = "household",
) -> dict:
    """Save uploaded file bytes and register the document record.

    Combines ``document_service.save_uploaded_file`` with
    ``create_document`` so the UI only supplies raw upload data and
    relation ids; all other metadata decisions (``source_module`` etc.)
    are resolved here in the service layer.
    """
    from app.services.document_service import save_uploaded_file  # local import avoids circular dep

    saved = save_uploaded_file(filename, file_bytes, source_module=source_module, visibility=visibility)
    return create_document(
        {
            **saved,
            "asset_id": asset_id,
            "project_id": project_id,
            "source_module": source_module,
            "visibility": visibility,
        }
    )


def create_event(payload: dict) -> dict:
    return create_record("events", payload)


def capture_inbox_entry(text: str) -> dict:
    lowered = text.lower()
    amount = None
    _, separator, amount_tail = lowered.partition(" til ")
    if separator:
        raw_amount = []
        started = False
        for char in amount_tail:
            if char.isdigit():
                raw_amount.append(char)
                started = True
                continue
            if char in {" ", "."} and started:
                raw_amount.append(char)
                continue
            if started:
                break
        cleaned_amount = "".join(raw_amount).replace(" ", "").replace(".", "")
        amount = cleaned_amount or None
    suggestions = []

    if "kjøp" in lowered or "kjøpe" in lowered:
        suggestions.append(
            {
                "object_type": "asset",
                "fields": {
                    "name": text[: lowered.find(" til ")].strip() if " til " in lowered else text.strip(),
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
            "visibility": "private",
        },
    )
    append_event(
        title=f"Innboksfangst: {text[:60]}",
        event_type="inbox_captured",
        notes=f"{len(suggestions)} forslag generert",
        visibility="private",
    )
    return inbox_item


_OBJECT_CREATORS = {
    "asset": create_asset,
    "task": create_task,
    "decision": create_decision,
    "project": create_project,
}


def apply_inbox_suggestion(inbox_id: str, suggestion_index: int) -> dict:
    """Create a record from an inbox suggestion and update inbox status."""
    inbox_item = get_record("inbox_items", inbox_id)
    if not inbox_item:
        raise ValueError("Inbox-element ikke funnet")

    suggestions = list(inbox_item.get("suggestions") or [])
    if suggestion_index < 0 or suggestion_index >= len(suggestions):
        raise ValueError("Ugyldig forslagsindeks")

    suggestion = suggestions[suggestion_index]
    object_type = suggestion.get("object_type")
    fields = suggestion.get("fields") or {}
    creator = _OBJECT_CREATORS.get(object_type)
    if creator is None:
        raise ValueError(f"Ukjent objekttype: {object_type}")

    fields = {**fields, "visibility": "household"}
    created = creator(fields)
    remaining = [s for i, s in enumerate(suggestions) if i != suggestion_index]
    status = "processed" if not remaining else "partial"
    update_record("inbox_items", inbox_id, {"suggestions": remaining, "status": status})
    append_event(
        title=f"Inbox-forslag brukt: {object_type}",
        event_type="inbox_suggestion_applied",
        notes=f"Opprettet {object_type}: {created.get('name') or created.get('title') or created.get('id')}",
    )
    return {"object_type": object_type, "created": created, "inbox_status": status}


def get_asset_detail(asset_id: str) -> dict | None:
    """Return an asset and all related records for asset-first navigation."""
    asset = get_record("assets", asset_id)
    if not asset:
        return None

    tasks = [t for t in list_records("tasks") if t.get("asset_id") == asset_id]
    projects = [p for p in list_records("projects") if p.get("asset_id") == asset_id]
    documents = [d for d in list_records("documents") if d.get("asset_id") == asset_id]
    decisions = [d for d in list_records("decisions") if d.get("asset_id") == asset_id]
    events = [e for e in list_records("events") if e.get("asset_id") == asset_id]
    open_tasks = [t for t in tasks if not t.get("completed")]

    return {
        "asset": asset,
        "tasks": tasks,
        "open_tasks": open_tasks,
        "projects": projects,
        "documents": documents,
        "decisions": decisions,
        "events": sorted(
            events,
            key=lambda event: event.get("event_date") or event.get("created_at", ""),
            reverse=True,
        ),
    }


def build_weekly_brief() -> dict:
    """Build a structured weekly brief — answers 'Hva bør jeg gjøre denne uka?'"""
    dashboard = build_dashboard_summary()
    decisions = list_records("decisions")
    open_decisions = [d for d in decisions if d.get("status") != "decided"][:5]

    lines = ["📋 Ukens brief", ""]
    metrics = dashboard["metrics"]
    lines.append(
        f"Du har {metrics['open_tasks']} åpne oppgaver, "
        f"{metrics['projects']} aktive prosjekter og "
        f"{metrics['open_decisions']} åpne beslutninger."
    )

    if dashboard["priorities"]:
        lines.append("\n**Prioriterte oppgaver:**")
        for task in dashboard["priorities"]:
            due = f" (frist: {task.get('due_date')})" if task.get("due_date") else ""
            lines.append(f"- {task['title']} [P{task.get('priority', 2)}]{due}")

    if dashboard["active_projects"]:
        lines.append("\n**Aktive prosjekter — neste handling:**")
        for project in dashboard["active_projects"]:
            next_action = project.get("next_action") or "Ikke satt"
            lines.append(f"- {project['name']}: {next_action}")

    if open_decisions:
        lines.append("\n**Åpne beslutninger:**")
        for decision in open_decisions:
            lines.append(f"- {decision['title']}")

    if dashboard["upcoming_events"]:
        lines.append("\n**Kommende hendelser:**")
        for event in dashboard["upcoming_events"]:
            lines.append(f"- {event['title']} ({event.get('event_date', 'dato ukjent')})")

    if not dashboard["priorities"] and not dashboard["active_projects"] and not open_decisions:
        lines.append("\nIngen presserende ting akkurat nå. Bra jobba!")

    return {
        "summary_text": "\n".join(lines),
        "priorities": dashboard["priorities"],
        "active_projects": dashboard["active_projects"],
        "open_decisions": open_decisions,
        "upcoming_events": dashboard["upcoming_events"],
        "metrics": dashboard["metrics"],
    }


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
