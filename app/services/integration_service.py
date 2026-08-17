"""User integrations — Outlook, Apple Health, Garmin, Strava."""

from __future__ import annotations

from datetime import datetime, timezone

from app.services.auth_context import get_current_context
from app.services.outlook_service import (
    _microsoft_configured,
    complete_outlook_oauth,
    start_outlook_oauth,
    sync_outlook_to_inbox,
)
from app.services.storage_service import create_record, list_records, update_record

PROVIDERS = {
    "outlook": {
        "label": "Microsoft Outlook",
        "description": "Kalender og e-postsignaler til Inbox",
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
                "configured": provider != "outlook" or _microsoft_configured(),
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
        "user_id": context.user_id,
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


def sync_provider(provider: str) -> dict:
    row = _integration_row(provider)
    if not row or row.get("status") not in {"connected", "error"}:
        raise RuntimeError(f"{provider} er ikke tilkoblet.")

    if provider == "outlook":
        return sync_outlook_to_inbox(row)

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


def start_outlook_connect() -> dict:
    context = get_current_context()
    if not context:
        raise RuntimeError("Ikke innlogget.")
    return start_outlook_oauth(context.user_id)


def finish_outlook_connect(code: str, state: str) -> dict:
    context = get_current_context()
    if not context:
        raise RuntimeError("Ikke innlogget.")
    return complete_outlook_oauth(code, state, context.user_id)
