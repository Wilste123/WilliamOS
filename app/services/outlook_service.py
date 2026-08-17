"""Microsoft Outlook / Graph integration — calendar + mail signals to Inbox."""

from __future__ import annotations

import json
import logging
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from app.services.action_engine import capture_inbox_entry
from app.services.storage_service import create_record, list_records, update_record

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
AUTH_BASE = "https://login.microsoftonline.com/common/oauth2/v2.0"
SCOPES = "offline_access Calendars.Read Mail.Read User.Read"


def _microsoft_configured() -> bool:
    return bool(
        (os.getenv("MICROSOFT_CLIENT_ID") or "").strip()
        and (os.getenv("MICROSOFT_CLIENT_SECRET") or "").strip()
        and (os.getenv("MICROSOFT_REDIRECT_URI") or "").strip()
    )


def _redirect_uri() -> str:
    return (
        os.getenv("MICROSOFT_REDIRECT_URI")
        or os.getenv("FRONTEND_URL")
        or "http://localhost:3000"
    ).rstrip("/") + "/integrations/callback"


def _http_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def _http_get(url: str, access_token: str) -> dict:
    request = urllib.request.Request(url, method="GET")
    request.add_header("Authorization", f"Bearer {access_token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def build_outlook_auth_url(oauth_state: str) -> str:
    params = {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID", ""),
        "response_type": "code",
        "redirect_uri": _redirect_uri(),
        "scope": SCOPES,
        "state": oauth_state,
        "response_mode": "query",
    }
    return f"{AUTH_BASE}/authorize?{urllib.parse.urlencode(params)}"


def exchange_outlook_code(code: str) -> dict:
    return _http_form(
        f"{AUTH_BASE}/token",
        {
            "client_id": os.getenv("MICROSOFT_CLIENT_ID", ""),
            "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET", ""),
            "code": code,
            "redirect_uri": _redirect_uri(),
            "grant_type": "authorization_code",
        },
    )


def refresh_outlook_token(refresh_token: str) -> dict:
    return _http_form(
        f"{AUTH_BASE}/token",
        {
            "client_id": os.getenv("MICROSOFT_CLIENT_ID", ""),
            "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET", ""),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )


def _ensure_access_token(integration: dict) -> str | None:
    access = integration.get("access_token")
    expires = integration.get("token_expires_at")
    refresh = integration.get("refresh_token")
    if not access:
        return None
    if expires:
        try:
            exp = datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
            if exp <= datetime.now(timezone.utc) + timedelta(minutes=2) and refresh:
                tokens = refresh_outlook_token(refresh)
                access = tokens["access_token"]
                update_record(
                    "user_integrations",
                    integration["id"],
                    {
                        "access_token": access,
                        "refresh_token": tokens.get("refresh_token") or refresh,
                        "token_expires_at": (
                            datetime.now(timezone.utc) + timedelta(seconds=int(tokens.get("expires_in", 3600)))
                        ).isoformat(),
                        "status": "connected",
                    },
                )
        except (urllib.error.URLError, KeyError, ValueError) as exc:
            logger.warning("Outlook token refresh failed: %s", exc)
            update_record("user_integrations", integration["id"], {"status": "error"})
            return None
    return access


def fetch_calendar_events(access_token: str, days: int = 7) -> list[dict]:
    start = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    end = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")
    url = (
        f"{GRAPH_BASE}/me/calendarview?startDateTime={urllib.parse.quote(start)}"
        f"&endDateTime={urllib.parse.quote(end)}&$top=15&$orderby=start/dateTime"
    )
    payload = _http_get(url, access_token)
    return payload.get("value") or []


def fetch_recent_emails(access_token: str, limit: int = 8) -> list[dict]:
    url = f"{GRAPH_BASE}/me/messages?$top={limit}&$orderby=receivedDateTime desc&$select=subject,receivedDateTime,isRead,from"
    payload = _http_get(url, access_token)
    return payload.get("value") or []


def sync_outlook_to_inbox(integration: dict) -> dict:
    """Pull calendar + mail highlights into Inbox signals."""
    access = _ensure_access_token(integration)
    if not access:
        raise RuntimeError("Outlook er ikke tilkoblet eller token er utløpt.")

    created = 0
    try:
        for event in fetch_calendar_events(access):
            title = event.get("subject") or "Kalenderhendelse"
            start = ((event.get("start") or {}).get("dateTime") or "")[:16].replace("T", " ")
            capture_inbox_entry(f"Outlook kalender: {title}" + (f" ({start})" if start else ""))
            created += 1

        for message in fetch_recent_emails(access):
            if message.get("isRead"):
                continue
            subject = message.get("subject") or "Uten emne"
            capture_inbox_entry(f"Outlook e-post: {subject}")
            created += 1
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Kunne ikke hente fra Outlook: {exc}") from exc

    update_record(
        "user_integrations",
        integration["id"],
        {"last_sync_at": datetime.now(timezone.utc).isoformat(), "status": "connected"},
    )
    return {"synced_signals": created, "provider": "outlook"}


def start_outlook_oauth(user_id: str) -> dict:
    if not _microsoft_configured():
        raise RuntimeError(
            "Microsoft Outlook er ikke konfigurert. Sett MICROSOFT_CLIENT_ID, "
            "MICROSOFT_CLIENT_SECRET og MICROSOFT_REDIRECT_URI i .env."
        )
    oauth_state = secrets.token_urlsafe(24)
    existing = next(
        (row for row in list_records("user_integrations") if row.get("provider") == "outlook"),
        None,
    )
    payload = {
        "provider": "outlook",
        "status": "pending",
        "metadata": {"oauth_state": oauth_state},
        "user_id": user_id,
    }
    if existing:
        update_record("user_integrations", existing["id"], payload)
    else:
        create_record("user_integrations", payload)

    return {"auth_url": build_outlook_auth_url(oauth_state), "configured": True}


def complete_outlook_oauth(code: str, state: str, user_id: str) -> dict:
    rows = list_records("user_integrations")
    integration = next(
        (
            row
            for row in rows
            if row.get("provider") == "outlook"
            and (row.get("metadata") or {}).get("oauth_state") == state
            and row.get("user_id") == user_id
        ),
        None,
    )
    if not integration:
        raise RuntimeError("Ugyldig OAuth-state. Prøv å koble til på nytt.")

    tokens = exchange_outlook_code(code)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(tokens.get("expires_in", 3600)))
    updated = update_record(
        "user_integrations",
        integration["id"],
        {
            "status": "connected",
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "token_expires_at": expires_at.isoformat(),
            "metadata": {},
        },
    )
    return updated or integration
