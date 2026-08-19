"""User integrations — Google, Apple Health, Garmin, Strava."""

from __future__ import annotations

from datetime import datetime, timezone

from app.services.auth_context import get_current_context
from app.services.google_service import (
    _google_configured,
    complete_google_oauth,
    start_google_oauth,
    sync_google_calendar_events,
    sync_google_to_inbox,
)
from app.services.storage_service import create_record, list_records, update_record

PROVIDERS = {
    "google": {
        "label": "Google Calendar & Gmail",
        "description": "Kalender (synk + opprett møter) og uleste e-poster som Inbox-signaler",
        "connect_type": "oauth",
    },
    "apple_health": {
        "label": "Apple Health",
        "description": "Vekt, søvn og aktivitet (krever iPhone-app)",
        "connect_type": "manual",
    },
    "garmin": {
        "label": "Garmin",
        "description": "Aktivitet og helsemetrics",
        "connect_type": "manual",
    },
    "strava": {
        "label": "Strava",
        "description": "Treningsaktivitet",
        "connect_type": "manual",
    },
}


def _user_integrations() -> list[dict]:
    try:
        return list_records("user_integrations")
    except Exception:
        return []


def _integration_row(provider: str) -> dict | None:
    return next((row for row in _user_integrations() if row.get("provider") == provider), None)


def list_integration_statuses() -> list[dict]:
    rows = {row.get("provider"): row for row in _user_integrations()}
    result = []
    for provider, meta in PROVIDERS.items():
        row = rows.get(provider)
        result.append(
            {
                "provider": provider,
                "label": meta["label"],
                "description": meta["description"],
                "connect_type": meta["connect_type"],
                "status": (row or {}).get("status", "disconnected"),
                "last_sync_at": (row or {}).get("last_sync_at"),
                "configured": provider != "google" or _google_configured(),
            }
        )
    return result


def connect_manual_provider(provider: str) -> dict:
    if provider not in PROVIDERS or PROVIDERS[provider]["connect_type"] != "manual":
        raise RuntimeError(f"Ukjent manuell integrasjon: {provider}")

    context = get_current_context()
    if not context:
        raise RuntimeError("Ikke innlogget.")

    existing = _integration_row(provider)
    payload = {
        "provider": provider,
        "status": "connected",
        "metadata": {"mode": "manual", "connected_at": datetime.now(timezone.utc).isoformat()},
    }
    if existing:
        return update_record("user_integrations", existing["id"], payload) or existing
    return create_record("user_integrations", payload)


def disconnect_provider(provider: str) -> dict:
    row = _integration_row(provider)
    if not row:
        return {"provider": provider, "status": "disconnected"}
    updated = update_record(
        "user_integrations",
        row["id"],
        {
            "status": "disconnected",
            "access_token": None,
            "refresh_token": None,
            "token_expires_at": None,
            "metadata": {},
        },
    )
    return updated or row


def sync_google_calendar_only() -> dict:
    row = _integration_row("google")
    if not row or row.get("status") not in {"connected", "error"}:
        raise RuntimeError("google er ikke tilkoblet.")
    return sync_google_calendar_events(row, days=30)


def sync_provider(provider: str) -> dict:
    row = _integration_row(provider)
    if not row or row.get("status") not in {"connected", "error"}:
        raise RuntimeError(f"{provider} er ikke tilkoblet.")

    if provider == "google":
        return sync_google_to_inbox(row)

    update_record(
        "user_integrations",
        row["id"],
        {"last_sync_at": datetime.now(timezone.utc).isoformat()},
    )
    return {
        "provider": provider,
        "synced_signals": 0,
        "message": "Manuell integrasjon — logg data i Helse-modulen.",
    }


def start_google_connect() -> dict:
    context = get_current_context()
    if not context:
        raise RuntimeError("Ikke innlogget.")
    return start_google_oauth(context.user_id)


def finish_google_connect(code: str, state: str) -> dict:
    context = get_current_context()
    if not context:
        raise RuntimeError("Ikke innlogget.")
    return complete_google_oauth(code, state, context.user_id)
