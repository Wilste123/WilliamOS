import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.database.supabase import get_supabase

logger = logging.getLogger(__name__)


def _require_supabase(operation: str, collection: str):
    """Return a live Supabase client or raise a clear RuntimeError."""
    sb = get_supabase()
    if sb is None:
        raise RuntimeError(
            f"Supabase is not configured. Cannot perform '{operation}' on '{collection}'. "
            "Set SUPABASE_URL and SUPABASE_KEY environment variables."
        )
    return sb


def list_records(collection: str, user_id: str | None = None) -> list[dict]:
    """Return all records for *collection* from Supabase.

    If *user_id* is provided, only records whose ``user_id`` column matches
    that value are returned (data isolation per authenticated user).
    """
    sb = _require_supabase("list_records", collection)
    query = sb.table(collection).select("*").order("created_at", desc=True)
    if user_id is not None:
        query = query.eq("user_id", user_id)
    response = query.execute()
    return response.data or []


def get_record(collection: str, record_id: str) -> dict | None:
    """Return a single record by id from Supabase."""
    sb = _require_supabase("get_record", collection)
    response = sb.table(collection).select("*").eq("id", record_id).maybe_single().execute()
    return response.data


def create_record(collection: str, payload: dict) -> dict:
    """Persist a new record to Supabase."""
    sb = _require_supabase("create_record", collection)
    record = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    response = sb.table(collection).insert(record).execute()
    if response.data:
        return response.data[0]
    raise RuntimeError(f"Supabase insert returned no data for '{collection}'")


def update_record(collection: str, record_id: str, updates: dict) -> dict | None:
    """Update an existing record in Supabase."""
    sb = _require_supabase("update_record", collection)
    patch = {**updates, "updated_at": datetime.now(timezone.utc).isoformat()}
    response = sb.table(collection).update(patch).eq("id", record_id).execute()
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
) -> dict:
    return create_record(
        "events",
        {
            "title": title,
            "event_type": event_type,
            "notes": notes,
            "asset_id": asset_id,
            "project_id": project_id,
            "decision_id": decision_id,
            "event_date": event_date,
        },
    )
