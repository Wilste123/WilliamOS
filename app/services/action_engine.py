import json
import logging
import re
from datetime import date, datetime, timezone

from app.services.openai_service import chat_completion
from app.services.storage_service import append_event, create_record, delete_record, get_record, list_records, update_record

logger = logging.getLogger(__name__)


def _normalize_suggestions(raw: object) -> list[dict]:
    """Return inbox suggestions as a list of dicts regardless of storage shape."""
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
    return []


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


def delete_document_record(document_id: str) -> bool:
    """Remove a document record and its storage object."""
    from app.services.document_storage import delete_document as remove_storage_file

    document = get_record("documents", document_id)
    if not document:
        return False
    storage_path = document.get("storage_path")
    if storage_path:
        try:
            remove_storage_file(str(storage_path))
        except RuntimeError as exc:
            logger.warning("Storage delete failed for %s: %s", document_id, exc)
    return delete_record("documents", document_id)


def reanalyze_document(document_id: str) -> dict:
    """Re-run document intelligence and route fresh suggestions to Inbox."""
    from app.services.document_intelligence import analyze_stored_document
    from app.services.document_storage import read_document_text

    document = get_record("documents", document_id)
    if not document:
        raise ValueError("Dokument ikke funnet")

    storage_path = document.get("storage_path")
    filename = document.get("filename") or "document"
    text_content = document.get("text_content")
    if not text_content and storage_path:
        text_content = read_document_text(str(storage_path), filename)
        if text_content:
            document = update_record(
                "documents",
                document_id,
                {"text_content": text_content},
            ) or document

    intelligence = analyze_stored_document(document)
    inbox_signal = capture_document_inbox_signal(document, intelligence)
    return {
        "document": document,
        "intelligence": intelligence,
        "inbox_signal": inbox_signal,
    }


def create_goal(payload: dict) -> dict:
    goal = create_record("goals", payload)
    append_event(
        title=f"Mål opprettet: {goal['title']}",
        event_type="goal_created",
        notes=goal.get("next_step"),
        visibility=goal.get("visibility"),
    )
    return goal


def update_goal(goal_id: str, updates: dict) -> dict | None:
    goal = update_record("goals", goal_id, updates)
    if goal:
        append_event(
            title=f"Mål oppdatert: {goal['title']}",
            event_type="goal_updated",
            notes=goal.get("next_step"),
            visibility=goal.get("visibility"),
        )
    return goal


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


def _parse_amount_from_text(text: str) -> float | None:
    lowered = text.lower()
    _, separator, amount_tail = lowered.partition(" til ")
    if not separator:
        return None
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
    if not cleaned_amount:
        return None
    try:
        return float(cleaned_amount)
    except ValueError:
        return None


def _extract_asset_name_from_email_text(text: str) -> str | None:
    """Pull a likely asset name from subjects like 'kjøpskontrakt - Mazda cx5'."""
    cleaned = re.sub(r"^google e-post:\s*", "", text.strip(), flags=re.IGNORECASE)
    if " - " in cleaned:
        candidate = cleaned.rsplit(" - ", 1)[-1].strip()
        if len(candidate) >= 2:
            return candidate
    return None


def _rule_based_inbox_suggestions(text: str) -> list[dict]:
    lowered = text.lower()
    amount = _parse_amount_from_text(text)
    suggestions = []
    asset_name_from_subject = _extract_asset_name_from_email_text(text)

    contract_keywords = (
        "kjøpskontrakt",
        "kjøpekontrakt",
        "salgskontrakt",
        "overtakelsesprotokoll",
        "kontrakt",
    )
    is_contract = any(keyword in lowered for keyword in contract_keywords)
    is_purchase = (
        "kjøp" in lowered or "kjøpe" in lowered or "vurderer" in lowered or is_contract
    )

    if is_purchase:
        if asset_name_from_subject:
            asset_name = asset_name_from_subject
        elif " til " in lowered:
            asset_name = text[: lowered.find(" til ")].strip()
        else:
            asset_name = text.strip()
        suggestions.append(
            {
                "object_type": "asset",
                "fields": {
                    "name": asset_name,
                    "status": "active" if is_contract else "considering_purchase",
                    "estimated_value": amount,
                    "description": text,
                },
            }
        )
        suggestions.append(
            {
                "object_type": "decision",
                "fields": {
                    "title": f"Kjøp: {asset_name}" if is_contract else f"Vurdere: {text[:60]}",
                    "summary": text,
                    "status": "open",
                },
            }
        )

    if "forsikring" in lowered:
        suggestions.append(
            {
                "object_type": "task",
                "fields": {
                    "title": "Sjekk forsikring",
                    "priority": 2,
                    "status": "open",
                    "notes": text,
                },
            }
        )
        if asset_name_from_subject:
            suggestions.append(
                {
                    "object_type": "asset",
                    "fields": {
                        "name": asset_name_from_subject,
                        "description": text,
                        "status": "active",
                    },
                }
            )

    if "faktura" in lowered or "invoice" in lowered:
        suggestions.append(
            {
                "object_type": "task",
                "fields": {
                    "title": "Behandle faktura",
                    "priority": 2,
                    "status": "open",
                    "notes": text,
                },
            }
        )

    if any(keyword in lowered for keyword in ["må", "skal", "trenger", "oppgave", "service", "bestille"]):
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

    return suggestions


def _llm_inbox_suggestions(text: str) -> list[dict]:
    prompt = (
        "Du klassifiserer innboksfangst for en personlig assistent. "
        "Returner KUN gyldig JSON med nøkkelen suggestions. "
        "Hver suggestion har object_type (asset, task, decision) og fields. "
        "For asset: name, status (considering_purchase/active), estimated_value (number eller null). "
        "For task: title, priority (1-3), status (open). "
        "For decision: title, summary, status (open)."
    )
    raw = chat_completion(
        [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.1,
    )
    if not raw or "OpenAI er ikke konfigurert" in raw or "OpenAI-kallet feilet" in raw:
        return []

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        payload = json.loads(raw[start:end]) if start >= 0 and end > start else {}
        suggestions = payload.get("suggestions", [])
        if isinstance(suggestions, list):
            return [item for item in suggestions if isinstance(item, dict) and item.get("object_type")]
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("LLM inbox parse failed: %s", exc)
    return []


def _build_inbox_suggestions(text: str) -> list[dict]:
    llm_suggestions = _llm_inbox_suggestions(text)
    if llm_suggestions:
        return llm_suggestions
    return _rule_based_inbox_suggestions(text)


def capture_inbox_entry(text: str, *, fast: bool = False) -> dict:
    suggestions = [] if fast else _build_inbox_suggestions(text)

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


_INBOX_METADATA_FIELDS = frozenset(
    {
        "gmail_message_id",
        "attachment_id",
        "filename",
        "asset_name_hint",
        "subject",
        "from_address",
        "snippet",
    }
)


def _payload_for_object_creator(object_type: str, fields: dict) -> dict:
    """Strip inbox-only metadata before persisting asset/task/decision/project records."""
    payload = {
        key: value
        for key, value in fields.items()
        if key not in _INBOX_METADATA_FIELDS and value is not None
    }
    if object_type == "task" and "notes" in payload and "description" not in payload:
        payload["description"] = payload.pop("notes")
    return payload


def build_google_email_suggestions(
    *,
    subject: str,
    snippet: str = "",
    from_address: str = "",
    gmail_message_id: str = "",
    attachment_meta: list[dict] | None = None,
) -> list[dict]:
    """Build inbox suggestions for a Gmail message without calling the LLM."""
    display_text = f"Google e-post: {subject}".strip()
    suggestions = _rule_based_inbox_suggestions(display_text)
    asset_name = _extract_asset_name_from_email_text(display_text)
    attachments = attachment_meta or []
    pdf_attachments = [
        item
        for item in attachments
        if str(item.get("filename", "")).lower().endswith(".pdf")
    ]

    for attachment in pdf_attachments:
        filename = attachment.get("filename") or "vedlegg.pdf"
        suggestions.append(
            {
                "object_type": "gmail_attachment",
                "fields": {
                    "gmail_message_id": gmail_message_id,
                    "attachment_id": attachment.get("attachment_id"),
                    "filename": filename,
                    "asset_name_hint": asset_name,
                    "subject": subject,
                    "from_address": from_address,
                    "snippet": snippet,
                },
            }
        )

    if not suggestions and (subject.strip() or snippet.strip()):
        suggestions.append(
            {
                "object_type": "task",
                "fields": {
                    "title": subject[:80] or "E-postoppfølging",
                    "notes": snippet or subject,
                    "priority": 2,
                    "status": "open",
                    "gmail_message_id": gmail_message_id,
                },
            }
        )

    return suggestions


def gmail_message_already_in_inbox(gmail_message_id: str, *, subject: str = "") -> bool:
    """Return True if this Gmail message was already captured as an inbox signal."""
    display_text = f"Google e-post: {subject}".strip() if subject else ""
    for item in list_records("inbox_items"):
        if display_text and item.get("text") == display_text:
            return bool(_normalize_suggestions(item.get("suggestions")))
        if not gmail_message_id:
            continue
        for suggestion in _normalize_suggestions(item.get("suggestions")):
            if (suggestion.get("fields") or {}).get("gmail_message_id") == gmail_message_id:
                return True
    return False


def capture_google_email_signal(
    *,
    subject: str,
    snippet: str = "",
    from_address: str = "",
    gmail_message_id: str = "",
    attachment_meta: list[dict] | None = None,
) -> dict | None:
    """Capture a Gmail message as an inbox item with rule-based suggestions."""
    display_text = f"Google e-post: {subject}".strip()
    suggestions = build_google_email_suggestions(
        subject=subject,
        snippet=snippet,
        from_address=from_address,
        gmail_message_id=gmail_message_id,
        attachment_meta=attachment_meta,
    )

    for item in list_records("inbox_items"):
        if item.get("text") != display_text:
            continue
        if _normalize_suggestions(item.get("suggestions")):
            return None
        updated = update_record(
            "inbox_items",
            item["id"],
            {
                "suggestions": suggestions,
                "signal_type": "gmail",
                "status": "captured",
            },
        )
        append_event(
            title=f"Gmail-signal oppdatert: {subject[:60]}",
            event_type="gmail_inbox_signal",
            notes=f"{len(suggestions)} forslag generert",
            visibility="private",
        )
        return updated

    inbox_item = create_record(
        "inbox_items",
        {
            "text": display_text,
            "signal_type": "gmail",
            "status": "captured",
            "suggestions": suggestions,
            "visibility": "private",
        },
    )
    append_event(
        title=f"Gmail-signal: {subject[:60]}",
        event_type="gmail_inbox_signal",
        notes=f"{len(suggestions)} forslag generert",
        visibility="private",
    )
    return inbox_item


def capture_document_inbox_signal(document: dict, intelligence: dict) -> dict | None:
    """Route uploaded document intelligence into Inbox — WilliamOS command center."""
    suggestions = intelligence.get("suggestions") or []
    if not suggestions:
        return None

    filename = document.get("filename") or "dokument"
    doc_type = intelligence.get("doc_type") or "other"
    primary_message = suggestions[0].get("message") or f"Nytt dokument: {filename}"

    inbox_suggestions = [
        {
            "object_type": "document",
            "fields": {
                "suggestion_id": item.get("id"),
                "label": item.get("label"),
                "message": item.get("message"),
                "document_id": document.get("id"),
                "payload": item.get("payload") or {},
            },
        }
        for item in suggestions
        if isinstance(item, dict)
    ]

    inbox_item = create_record(
        "inbox_items",
        {
            "text": primary_message,
            "suggestions": inbox_suggestions,
            "status": "captured",
            "signal_type": "document",
            "document_id": document.get("id"),
            "doc_type": doc_type,
            "visibility": "private",
        },
    )
    append_event(
        title=f"Dokumentsignal: {filename}",
        event_type="document_inbox_signal",
        notes=f"{doc_type} · {len(inbox_suggestions)} forslag",
        visibility="private",
    )
    return inbox_item


def dismiss_inbox_item(inbox_id: str) -> dict:
    """Mark an inbox item as ignored/processed without applying suggestions."""
    inbox_item = get_record("inbox_items", inbox_id)
    if not inbox_item:
        raise ValueError("Inbox-element ikke funnet")
    updated = update_record("inbox_items", inbox_id, {"status": "ignored", "suggestions": []})
    append_event(
        title=f"Inbox ignorert: {(inbox_item.get('text') or '')[:60]}",
        event_type="inbox_dismissed",
        visibility="private",
    )
    return {"inbox_status": "ignored", "item": updated}


def apply_document_suggestion_action(document_id: str, suggestion_id: str, payload: dict | None = None) -> dict:
    """Execute a document intelligence suggestion (link asset, update insurance, create task)."""
    payload = payload or {}
    document = get_record("documents", document_id)
    if not document:
        raise ValueError("Dokument ikke funnet")

    if suggestion_id == "link_asset":
        asset_id = payload.get("asset_id")
        if not asset_id:
            raise ValueError("asset_id required")
        updated = update_record("documents", document_id, {"asset_id": asset_id})
        return {"applied": True, "document": updated, "action": "link_asset"}

    if suggestion_id == "update_insurance":
        asset_id = payload.get("asset_id")
        if not asset_id:
            raise ValueError("asset_id required")
        note = f"Forsikring oppdatert via dokument: {document.get('filename')}"
        asset = update_asset(asset_id, {"description": note})
        update_record("documents", document_id, {"asset_id": asset_id})
        return {"applied": True, "asset": asset, "action": "update_insurance"}

    if suggestion_id == "create_service_task":
        task = create_task(
            {
                "title": payload.get("title") or f"Service: {document.get('filename')}",
                "asset_id": payload.get("asset_id") or document.get("asset_id"),
                "priority": payload.get("priority", 2),
                "status": "open",
            }
        )
        return {"applied": True, "task": task, "action": "create_service_task"}

    raise ValueError(f"Ukjent dokumentforslag: {suggestion_id}")


def apply_gmail_attachment_suggestion(fields: dict) -> dict:
    """Download a Gmail PDF attachment and register it as a document."""
    from app.services.google_service import download_gmail_attachment, get_connected_google_access_token

    message_id = fields.get("gmail_message_id")
    attachment_id = fields.get("attachment_id")
    filename = fields.get("filename") or "vedlegg.pdf"
    if not message_id or not attachment_id:
        raise ValueError("Gmail-vedlegg mangler message_id eller attachment_id")

    access_token = get_connected_google_access_token()
    if not access_token:
        raise RuntimeError("Google er ikke tilkoblet")

    file_bytes = download_gmail_attachment(access_token, str(message_id), str(attachment_id))

    asset_id = None
    hint = fields.get("asset_name_hint")
    if hint:
        for asset in list_records("assets"):
            if (asset.get("name") or "").lower() == str(hint).lower():
                asset_id = asset["id"]
                break

    document = save_document(
        str(filename),
        file_bytes,
        asset_id=asset_id,
        source_module="gmail",
    )
    return {"applied": True, "document": document, "action": "gmail_attachment"}


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

    suggestions = _normalize_suggestions(inbox_item.get("suggestions"))
    if suggestion_index < 0 or suggestion_index >= len(suggestions):
        raise ValueError("Ugyldig forslagsindeks")

    suggestion = suggestions[suggestion_index]
    object_type = suggestion.get("object_type")
    fields = suggestion.get("fields") or {}

    if object_type == "document":
        document_id = fields.get("document_id") or inbox_item.get("document_id")
        suggestion_id = fields.get("suggestion_id")
        if not document_id or not suggestion_id:
            raise ValueError("Dokumentforslag mangler document_id eller suggestion_id")
        result = apply_document_suggestion_action(
            str(document_id),
            str(suggestion_id),
            fields.get("payload") or {},
        )
        remaining = [s for i, s in enumerate(suggestions) if i != suggestion_index]
        status = "processed" if not remaining else "partial"
        update_record("inbox_items", inbox_id, {"suggestions": remaining, "status": status})
        append_event(
            title=f"Dokumentforslag brukt: {suggestion_id}",
            event_type="inbox_suggestion_applied",
            notes=str(result.get("action")),
        )
        return {"object_type": "document", "created": result, "inbox_status": status}

    if object_type == "gmail_attachment":
        result = apply_gmail_attachment_suggestion(fields)
        remaining = [s for i, s in enumerate(suggestions) if i != suggestion_index]
        status = "processed" if not remaining else "partial"
        update_record("inbox_items", inbox_id, {"suggestions": remaining, "status": status})
        append_event(
            title=f"Gmail-vedlegg importert: {fields.get('filename')}",
            event_type="inbox_suggestion_applied",
            notes="gmail_attachment",
        )
        return {"object_type": "gmail_attachment", "created": result, "inbox_status": status}

    creator = _OBJECT_CREATORS.get(object_type)
    if creator is None:
        raise ValueError(f"Ukjent objekttype: {object_type}")

    fields = {**_payload_for_object_creator(object_type, fields), "visibility": "household"}
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
    engine = build_priority_engine()
    dashboard = build_dashboard_summary()
    net_worth_nok = engine["net_worth_nok"]
    today = date.today().isoformat()

    overdue_tasks = [
        item
        for item in engine["items"]
        if item["source_type"] == "task" and item.get("meta", {}).get("overdue")
    ][:5]

    lines = ["📋 Ukens brief", ""]
    metrics = dashboard["metrics"]
    lines.append(
        f"Formue: {format_net_worth_nok(net_worth_nok) if net_worth_nok else '—'}. "
        f"Du har {metrics['open_tasks']} åpne oppgaver, "
        f"{metrics['projects']} aktive prosjekter og "
        f"{metrics['open_decisions']} åpne beslutninger."
    )

    if overdue_tasks:
        lines.append("\n**Forfalt — gjør først:**")
        for item in overdue_tasks:
            due = item.get("meta", {}).get("due_date")
            due_text = f" (frist: {str(due)[:10]})" if due else ""
            lines.append(f"- {item['title']}{due_text}")

    top_items = engine["items"][:5]
    if top_items:
        lines.append("\n**Topp 5 fokus denne uka:**")
        for index, item in enumerate(top_items, start=1):
            reason = item.get("reason")
            suffix = f" — {reason}" if reason else ""
            lines.append(f"{index}. {item['title']}{suffix}")

    if not top_items:
        lines.append("\nIngen presserende ting akkurat nå. Bra jobba!")

    task_priorities = [
        item["record"]
        for item in engine["items"]
        if item["source_type"] == "task" and item.get("record")
    ][:5]

    return {
        "summary_text": "\n".join(lines),
        "priorities": task_priorities,
        "focus_items": top_items,
        "overdue_tasks": [item["record"] for item in overdue_tasks if item.get("record")],
        "net_worth_nok": net_worth_nok,
        "net_worth_formatted": format_net_worth_nok(net_worth_nok) if net_worth_nok else "—",
        "active_projects": dashboard["active_projects"],
        "open_decisions": [
            d for d in list_records("decisions") if d.get("status") != "decided"
        ][:5],
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

    open_tasks = [
        task for task in tasks if not task.get("completed") and task.get("status") != "completed"
    ]
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


def _safe_list_records(collection: str) -> list[dict]:
    try:
        return list_records(collection)
    except Exception:
        return []


def format_net_worth_nok(amount: float) -> str:
    """Format NOK amount for home screen display."""
    if amount >= 1_000_000:
        millions = amount / 1_000_000
        text = f"{millions:.1f}".replace(".", ",")
        if text.endswith(",0"):
            text = text[:-2]
        return f"{text} MNOK"
    if amount >= 1_000:
        return f"{round(amount / 1_000):,} kNOK".replace(",", " ")
    return f"{round(amount):,} NOK".replace(",", " ")


def build_home_summary(display_name: str | None = None) -> dict:
    """Compact summary for the app home/start screen."""
    engine = build_priority_engine()
    dashboard = build_dashboard_summary()
    net_worth_nok = engine["net_worth_nok"]

    goals = _safe_list_records("goals")
    active_goals = len(
        [goal for goal in goals if goal.get("status", "active") in {"active", "open", "in_progress"}]
    )

    priority_titles = [item["title"] for item in engine["items"][:3] if item.get("title")]

    first_name = (display_name or "der").split()[0]

    return {
        "greeting_name": first_name,
        "net_worth_nok": net_worth_nok,
        "net_worth_formatted": format_net_worth_nok(net_worth_nok) if net_worth_nok else "—",
        "active_goals": active_goals,
        "open_tasks": dashboard["metrics"]["open_tasks"],
        "priorities": priority_titles,
        "focus_items": engine["items"][:5],
        "metrics": dashboard["metrics"],
    }


def _parse_date_only(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _priority_item(
    *,
    source_type: str,
    title: str,
    score: float,
    reason: str,
    record: dict | None = None,
    meta: dict | None = None,
) -> dict:
    return {
        "source_type": source_type,
        "title": title,
        "score": score,
        "reason": reason,
        "record": record,
        "meta": meta or {},
    }


def build_priority_engine(limit: int = 5) -> dict:
    """Merge tasks, goals, projects, inbox and assets into a ranked focus list."""
    from app.services.finance_service import compute_net_worth

    today = date.today()
    items: list[dict] = []

    assets = list_records("assets")
    finance = compute_net_worth()
    net_worth_nok = finance["net_worth_nok"]

    open_tasks = [
        task
        for task in list_records("tasks")
        if not task.get("completed") and task.get("status") != "completed"
    ]
    for task in open_tasks:
        due = _parse_date_only(task.get("due_date"))
        priority = int(task.get("priority") or 2)
        overdue = bool(due and due < today)
        due_soon = bool(due and today <= due <= date.fromordinal(today.toordinal() + 7))
        if overdue:
            score = 100 + priority * 10
            reason = "Forfalt oppgave"
        elif due_soon:
            score = 80 + priority * 10
            reason = "Frist innen 7 dager"
        else:
            score = 40 + priority * 5
            reason = f"Prioritet P{priority}"
        items.append(
            _priority_item(
                source_type="task",
                title=task["title"],
                score=score,
                reason=reason,
                record=task,
                meta={"overdue": overdue, "due_date": task.get("due_date"), "priority": priority},
            )
        )

    for project in list_records("projects"):
        if project.get("status") != "active":
            continue
        next_action = (project.get("next_action") or "").strip()
        title = f"{project['name']}: {next_action}" if next_action else project["name"]
        items.append(
            _priority_item(
                source_type="project",
                title=title,
                score=50,
                reason="Aktivt prosjekt",
                record=project,
            )
        )

    for goal in _safe_list_records("goals"):
        if goal.get("status") not in {"active", "open", "in_progress"}:
            continue
        next_step = (goal.get("next_step") or "").strip()
        title = f"{goal['title']}: {next_step}" if next_step else goal["title"]
        target = _parse_date_only(goal.get("target_date"))
        score = 55
        reason = "Aktivt mål"
        if target and target <= date.fromordinal(today.toordinal() + 14):
            score = 65
            reason = "Mål med nær frist"
        items.append(
            _priority_item(
                source_type="goal",
                title=title,
                score=score,
                reason=reason,
                record=goal,
            )
        )

    for inbox_item in list_records("inbox_items"):
        if inbox_item.get("status") in {"processed", "ignored"}:
            continue
        if inbox_item.get("signal_type") == "document":
            items.append(
                _priority_item(
                    source_type="inbox",
                    title=(inbox_item.get("text") or "Dokumentsignal")[:80],
                    score=70,
                    reason="Ubehandlet dokumentsignal",
                    record=inbox_item,
                )
            )
            continue
        suggestions = _normalize_suggestions(inbox_item.get("suggestions"))
        task_suggestions = [s for s in suggestions if s.get("object_type") == "task"]
        if not task_suggestions:
            continue
        fields = task_suggestions[0].get("fields") or {}
        title = fields.get("title") or inbox_item.get("text", "Inbox-forslag")[:80]
        items.append(
            _priority_item(
                source_type="inbox",
                title=title,
                score=60,
                reason="Ubehandlet inbox-forslag",
                record=inbox_item,
                meta={"suggestion_index": suggestions.index(task_suggestions[0])},
            )
        )

    for decision in list_records("decisions"):
        if decision.get("status") == "decided":
            continue
        items.append(
            _priority_item(
                source_type="decision",
                title=decision["title"],
                score=45,
                reason="Åpen beslutning",
                record=decision,
            )
        )

    ranked = sorted(items, key=lambda item: (-item["score"], item["title"]))[:limit]
    return {
        "items": ranked,
        "net_worth_nok": net_worth_nok,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
