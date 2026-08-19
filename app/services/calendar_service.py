"""Calendar events — internal schedule + Google Calendar sync."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.services.google_service import (
    create_google_calendar_event,
    delete_google_calendar_event,
    get_connected_google_integration,
    google_has_calendar_write_scope,
    sync_google_calendar_events,
    update_google_calendar_event,
)
from app.services.storage_service import create_record, delete_record, list_records, update_record

logger = logging.getLogger(__name__)

COLLECTION = "calendar_events"


def _list_records_safe() -> list[dict]:
    try:
        return list_records(COLLECTION)
    except Exception:
        return []


def _parse_dt(value: object | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _serialize_event(record: dict, *, google_synced: bool | None = None, google_sync_error: str | None = None) -> dict:
    """Expose start_at for consumers that expect event_date."""
    out = dict(record)
    if out.get("start_at") and not out.get("event_date"):
        out["event_date"] = out["start_at"]
    if google_synced is not None:
        out["google_synced"] = google_synced
    if google_sync_error:
        out["google_sync_error"] = google_sync_error
    return out


def _google_write_scope_error() -> str:
    return (
        "Google mangler skrivetilgang til kalender. "
        "Gå til Integrasjoner og trykk «Oppdater Google-tilgang»."
    )


def _apply_google_metadata(record: dict, google_event: dict) -> dict:
    updated = update_record(
        COLLECTION,
        record["id"],
        {
            "source": "google",
            "external_id": google_event.get("id"),
            "calendar_id": google_event.get("organizer", {}).get("email") or "primary",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return updated or record


def _push_record_to_google(record: dict, *, update: bool = False) -> tuple[dict, str | None]:
    """Write or update a record in Google Calendar. Returns (record, error_message)."""
    integration = get_connected_google_integration()
    if not integration:
        return record, "Google er ikke tilkoblet."

    if not google_has_calendar_write_scope(integration):
        return record, _google_write_scope_error()

    try:
        if update and record.get("external_id"):
            google_event = update_google_calendar_event(integration, record)
        else:
            google_event = create_google_calendar_event(integration, record)
        return _apply_google_metadata(record, google_event), None
    except Exception as exc:
        message = str(exc)
        logger.warning("Google calendar write-back failed: %s", message)
        return record, message


def list_calendar_events(
    *,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    days: int | None = None,
    limit: int = 100,
) -> list[dict]:
    now = datetime.now(timezone.utc)
    range_start = _parse_dt(from_date) or now
    if days is not None and to_date is None:
        range_end = range_start + timedelta(days=max(1, days))
    else:
        range_end = _parse_dt(to_date) or (range_start + timedelta(days=30))

    rows = _list_records_safe()
    filtered: list[dict] = []
    for row in rows:
        start_at = _parse_dt(row.get("start_at"))
        if start_at is None:
            continue
        if start_at < range_start or start_at > range_end:
            continue
        filtered.append(_serialize_event(row))

    return sorted(filtered, key=lambda row: row.get("start_at") or "")[:limit]


def list_upcoming(days: int = 7, limit: int = 20) -> list[dict]:
    return list_calendar_events(days=days, limit=limit)


def get_calendar_event(event_id: str) -> dict | None:
    rows = _list_records_safe()
    return next((row for row in rows if str(row.get("id")) == event_id), None)


def create_calendar_event(payload: dict, *, sync_google: bool = True) -> dict:
    body = {
        "title": payload["title"],
        "description": payload.get("description"),
        "location": payload.get("location"),
        "start_at": payload["start_at"],
        "end_at": payload.get("end_at"),
        "all_day": bool(payload.get("all_day", False)),
        "visibility": payload.get("visibility") or "household",
        "source": "internal",
        "asset_id": payload.get("asset_id"),
        "project_id": payload.get("project_id"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    record = create_record(COLLECTION, body)

    google_synced: bool | None = None
    google_sync_error: str | None = None
    if sync_google:
        integration = get_connected_google_integration()
        if integration:
            record, google_sync_error = _push_record_to_google(record)
            google_synced = google_sync_error is None
        else:
            google_synced = False
            google_sync_error = "Google er ikke tilkoblet."

    return _serialize_event(
        record,
        google_synced=google_synced,
        google_sync_error=google_sync_error,
    )


def update_calendar_event(event_id: str, updates: dict, *, sync_google: bool = True) -> dict | None:
    existing = get_calendar_event(event_id)
    if not existing:
        return None

    clean = {k: v for k, v in updates.items() if v is not None and k != "sync_google"}
    clean["updated_at"] = datetime.now(timezone.utc).isoformat()
    record = update_record(COLLECTION, event_id, clean)
    if not record:
        return None

    google_synced: bool | None = None
    google_sync_error: str | None = None
    if sync_google:
        integration = get_connected_google_integration()
        if integration:
            record, google_sync_error = _push_record_to_google(
                record,
                update=bool(record.get("external_id")),
            )
            google_synced = google_sync_error is None
        else:
            google_synced = False
            google_sync_error = "Google er ikke tilkoblet."

    return _serialize_event(
        record,
        google_synced=google_synced,
        google_sync_error=google_sync_error,
    )


def delete_calendar_event(event_id: str) -> bool:
    existing = get_calendar_event(event_id)
    if not existing:
        return False

    if existing.get("external_id"):
        integration = get_connected_google_integration()
        if integration:
            try:
                delete_google_calendar_event(
                    integration,
                    existing.get("external_id"),
                    calendar_id=existing.get("calendar_id") or "primary",
                )
            except Exception:
                pass

    return delete_record(COLLECTION, event_id)


def sync_google_calendar(integration: dict | None = None, *, days: int = 30) -> dict:
    row = integration or get_connected_google_integration()
    if not row:
        raise RuntimeError("Google er ikke tilkoblet.")
    return sync_google_calendar_events(row, days=days)
