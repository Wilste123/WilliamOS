"""Supabase persistence with enforced user/household scoping."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.database.supabase import get_authenticated_client, response_data
from app.services.auth_context import (
    UserContext,
    get_cached_supabase_client,
    get_current_context,
    set_cached_supabase_client,
)

logger = logging.getLogger(__name__)

DEFAULT_VISIBILITY = {
    "assets": "household",
    "projects": "household",
    "tasks": "household",
    "documents": "household",
    "decisions": "household",
    "events": "household",
    "goals": "household",
    "finance_accounts": "household",
    "finance_snapshots": "household",
    "health_metrics": "private",
    "inbox_items": "private",
    "memory_items": "private",
    "requests_log": "private",
    "chat_history": "private",
    "usage_log": "private",
}

# Only user_id — no visibility / household_id columns
USER_ONLY_COLLECTIONS = frozenset({"user_integrations", "usage_log"})

IMMUTABLE_AUTH_FIELDS = frozenset({"user_id", "household_id", "visibility"})


def _require_auth_context() -> UserContext:
    context = get_current_context()
    if context is None or not context.user_id:
        raise RuntimeError("Du må være innlogget for å få tilgang til data.")
    return context


def _record_visibility(record: dict, collection: str) -> str:
    visibility = record.get("visibility")
    if visibility in {"private", "household"}:
        return visibility
    return DEFAULT_VISIBILITY.get(collection, "household")


def can_access_record(record: dict, context: UserContext, collection: str) -> bool:
    """Return True when the signed-in user may read the record."""
    if collection in USER_ONLY_COLLECTIONS:
        return record.get("user_id") == context.user_id

    visibility = _record_visibility(record, collection)
    if visibility == "private":
        return record.get("user_id") == context.user_id

    household_id = record.get("household_id")
    return (
        household_id is not None
        and context.household_id is not None
        and household_id == context.household_id
    )


def _apply_read_scope(query, collection: str, context: UserContext):
    """Apply explicit read filters in addition to Supabase RLS."""
    if collection in USER_ONLY_COLLECTIONS:
        return query.eq("user_id", context.user_id)

    if not context.household_id:
        return query.eq("user_id", context.user_id).eq("visibility", "private")

    return query.or_(
        f"and(visibility.eq.private,user_id.eq.{context.user_id}),"
        f"and(visibility.eq.household,household_id.eq.{context.household_id})"
    )


def get_client():
    """Return a Supabase client scoped to the signed-in user (RLS applies)."""
    cached = get_cached_supabase_client()
    if cached is not None:
        return cached

    context = _require_auth_context()
    if not context.access_token or not context.refresh_token:
        raise RuntimeError("Sesjonen mangler tokens. Logg inn på nytt.")
    client = get_authenticated_client(
        context.access_token,
        context.refresh_token,
        validate_session=False,
    )
    set_cached_supabase_client(client)
    return client


def _require_supabase(operation: str, collection: str):
    """Return a live authenticated Supabase client or raise."""
    client = get_client()
    if client is None:
        raise RuntimeError(
            f"Supabase is not configured. Cannot perform '{operation}' on '{collection}'. "
            "Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
        )
    return client


def _reraise_if_jwt_expired(exc: Exception) -> None:
    message = str(getattr(exc, "message", None) or exc).lower()
    code = str(getattr(exc, "code", "") or "").lower()
    if code == "pgrst303" or "jwt expired" in message or "pgrst303" in message:
        raise RuntimeError("Sesjonen er utløpt. Logg inn på nytt.") from exc


def _execute_query(query):
    try:
        return query.execute()
    except Exception as exc:
        _reraise_if_jwt_expired(exc)
        raise


def _apply_auth_fields(collection: str, payload: dict) -> dict:
    """Stamp ownership from the current session — callers cannot override user/household."""
    context = _require_auth_context()
    record = {**payload}

    if collection in USER_ONLY_COLLECTIONS:
        record["user_id"] = context.user_id
        record.pop("household_id", None)
        record.pop("visibility", None)
        return record

    visibility = payload.get("visibility") or DEFAULT_VISIBILITY.get(collection, "household")
    if visibility not in {"private", "household"}:
        visibility = DEFAULT_VISIBILITY.get(collection, "household")

    record["user_id"] = context.user_id
    record["visibility"] = visibility

    if visibility == "household":
        if not context.household_id:
            raise RuntimeError("Household membership required for shared records.")
        record["household_id"] = context.household_id
    else:
        record["household_id"] = None

    return record


def _sanitize_update_patch(updates: dict) -> dict:
    """Prevent moving records across users or households via PATCH."""
    return {key: value for key, value in updates.items() if key not in IMMUTABLE_AUTH_FIELDS}


def list_records(collection: str) -> list[dict]:
    """Return records visible to the current user."""
    context = _require_auth_context()
    client = _require_supabase("list_records", collection)
    query = _apply_read_scope(
        client.table(collection).select("*").order("created_at", desc=True),
        collection,
        context,
    )
    response = _execute_query(query)
    rows = response_data(response, []) or []
    return [row for row in rows if can_access_record(row, context, collection)]


def get_record(collection: str, record_id: str) -> dict | None:
    """Return a single record if the current user may access it."""
    context = _require_auth_context()
    client = _require_supabase("get_record", collection)
    query = _apply_read_scope(
        client.table(collection).select("*").eq("id", record_id).limit(1),
        collection,
        context,
    )
    response = _execute_query(query)
    row = response_data(response, [])
    if not row:
        return None
    record = row[0]
    if not can_access_record(record, context, collection):
        return None
    return record


def create_record(collection: str, payload: dict) -> dict:
    """Persist a new record owned by the current user/household."""
    client = _require_supabase("create_record", collection)
    record = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        **_apply_auth_fields(collection, payload),
    }
    response = _execute_query(client.table(collection).insert(record))
    data = response_data(response, [])
    if data:
        return data[0]
    raise RuntimeError(f"Supabase insert returned no data for '{collection}'")


def update_record(collection: str, record_id: str, updates: dict) -> dict | None:
    """Update an existing record if the current user may access it."""
    context = _require_auth_context()
    client = _require_supabase("update_record", collection)
    patch = {**_sanitize_update_patch(updates), "updated_at": datetime.now(timezone.utc).isoformat()}
    query = _apply_read_scope(
        client.table(collection).update(patch).eq("id", record_id),
        collection,
        context,
    )
    response = _execute_query(query)
    data = response_data(response, [])
    if not data:
        return None
    record = data[0]
    if not can_access_record(record, context, collection):
        return None
    return record


def delete_record(collection: str, record_id: str) -> bool:
    """Delete a single record if the current user may access it."""
    existing = get_record(collection, record_id)
    if not existing:
        return False
    delete_records(collection, [record_id])
    return True


def delete_records(collection: str, record_ids: list[str] | None = None) -> int:
    """Delete records visible to the current user."""
    context = _require_auth_context()
    client = _require_supabase("delete_records", collection)
    if record_ids:
        deleted = 0
        for record_id in record_ids:
            query = _apply_read_scope(
                client.table(collection).delete().eq("id", record_id),
                collection,
                context,
            )
            _execute_query(query)
            deleted += 1
        return deleted
    rows = list_records(collection)
    deleted = 0
    for row in rows:
        _execute_query(client.table(collection).delete().eq("id", row["id"]))
        deleted += 1
    return deleted


def append_event(
    title: str,
    event_type: str,
    notes: str | None = None,
    *,
    asset_id: str | None = None,
    project_id: str | None = None,
    decision_id: str | None = None,
    event_date: str | None = None,
    visibility: str | None = None,
) -> dict:
    payload = {
        "title": title,
        "event_type": event_type,
        "notes": notes,
        "asset_id": asset_id,
        "project_id": project_id,
        "decision_id": decision_id,
        "event_date": event_date,
    }
    if visibility:
        payload["visibility"] = visibility
    event = create_record("events", payload)
    try:
        from app.services.memory_service import append_memory_from_event

        append_memory_from_event(event_type, title, notes)
    except Exception:
        pass
    return event
