"""Supabase persistence with enforced user/household scoping."""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.database.supabase import get_authenticated_client, response_data
from app.services.auth_context import UserContext, get_current_context

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
        raise RuntimeError("Authentication required. Sign in to access data.")
    return context


def get_client():
    """Return a Supabase client scoped to the signed-in user (RLS applies)."""
    context = _require_auth_context()
    if not context.access_token or not context.refresh_token:
        raise RuntimeError("Authentication required. Missing session tokens.")
    return get_authenticated_client(context.access_token, context.refresh_token)


def _require_supabase(operation: str, collection: str):
    """Return a live authenticated Supabase client or raise."""
    client = get_client()
    if client is None:
        raise RuntimeError(
            f"Supabase is not configured. Cannot perform '{operation}' on '{collection}'. "
            "Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
        )
    return client


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
    """Return records visible to the current user via Supabase RLS."""
    client = _require_supabase("list_records", collection)
    response = client.table(collection).select("*").order("created_at", desc=True).execute()
    return response_data(response, []) or []


def get_record(collection: str, record_id: str) -> dict | None:
    """Return a single record if RLS allows access."""
    client = _require_supabase("get_record", collection)
    response = client.table(collection).select("*").eq("id", record_id).limit(1).execute()
    row = response_data(response, [])
    if not row:
        return None
    return row[0]


def create_record(collection: str, payload: dict) -> dict:
    """Persist a new record owned by the current user/household."""
    client = _require_supabase("create_record", collection)
    record = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        **_apply_auth_fields(collection, payload),
    }
    response = client.table(collection).insert(record).execute()
    data = response_data(response, [])
    if data:
        return data[0]
    raise RuntimeError(f"Supabase insert returned no data for '{collection}'")


def update_record(collection: str, record_id: str, updates: dict) -> dict | None:
    """Update an existing record if RLS allows access."""
    client = _require_supabase("update_record", collection)
    patch = {**_sanitize_update_patch(updates), "updated_at": datetime.now(timezone.utc).isoformat()}
    response = client.table(collection).update(patch).eq("id", record_id).execute()
    data = response_data(response, [])
    if data:
        return data[0]
    return None


def delete_records(collection: str, record_ids: list[str] | None = None) -> int:
    """Delete records visible to the current user."""
    client = _require_supabase("delete_records", collection)
    if record_ids:
        deleted = 0
        for record_id in record_ids:
            client.table(collection).delete().eq("id", record_id).execute()
            deleted += 1
        return deleted
    rows = list_records(collection)
    deleted = 0
    for row in rows:
        client.table(collection).delete().eq("id", row["id"]).execute()
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
    return create_record("events", payload)
