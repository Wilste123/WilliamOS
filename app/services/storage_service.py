import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.database.supabase import get_authenticated_client, get_supabase
from app.services.auth_context import get_current_context

logger = logging.getLogger(__name__)

DEFAULT_VISIBILITY = {
    "assets": "household",
    "projects": "household",
    "tasks": "household",
    "documents": "household",
    "decisions": "household",
    "events": "household",
    "inbox_items": "private",
    "memory_items": "private",
    "requests_log": "private",
    "chat_history": "private",
}


def get_client():
    """Return an authenticated client when logged in, otherwise the anon client."""
    context = get_current_context()
    if context and context.access_token and context.refresh_token:
        return get_authenticated_client(context.access_token, context.refresh_token)
    return get_supabase()


def _require_supabase(operation: str, collection: str):
    """Return a live Supabase client or raise a clear RuntimeError."""
    client = get_client()
    if client is None:
        raise RuntimeError(
            f"Supabase is not configured. Cannot perform '{operation}' on '{collection}'. "
            "Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
        )
    return client


def _apply_auth_fields(collection: str, payload: dict) -> dict:
    context = get_current_context()
    if context is None:
        return payload

    record = {**payload}
    record.setdefault("user_id", context.user_id)
    record.setdefault("visibility", DEFAULT_VISIBILITY.get(collection, "household"))

    if record["visibility"] == "household":
        record.setdefault("household_id", context.household_id)
    else:
        record["household_id"] = None

    return record


def list_records(collection: str) -> list[dict]:
    """Return all records for *collection* from Supabase."""
    client = _require_supabase("list_records", collection)
    response = client.table(collection).select("*").order("created_at", desc=True).execute()
    return response.data or []


def get_record(collection: str, record_id: str) -> dict | None:
    """Return a single record by id from Supabase."""
    client = _require_supabase("get_record", collection)
    response = client.table(collection).select("*").eq("id", record_id).maybe_single().execute()
    return response.data


def create_record(collection: str, payload: dict) -> dict:
    """Persist a new record to Supabase."""
    client = _require_supabase("create_record", collection)
    record = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        **_apply_auth_fields(collection, payload),
    }
    response = client.table(collection).insert(record).execute()
    if response.data:
        return response.data[0]
    raise RuntimeError(f"Supabase insert returned no data for '{collection}'")


def update_record(collection: str, record_id: str, updates: dict) -> dict | None:
    """Update an existing record in Supabase."""
    client = _require_supabase("update_record", collection)
    patch = {**updates, "updated_at": datetime.now(timezone.utc).isoformat()}
    response = client.table(collection).update(patch).eq("id", record_id).execute()
    if response.data:
        return response.data[0]
    return None


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
