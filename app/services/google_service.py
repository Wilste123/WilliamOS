"""Google Calendar + Gmail integration — calendar and mail signals to Inbox."""

from __future__ import annotations

import base64
import json
import logging
import os
import secrets
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from app.services.action_engine import (
    capture_google_email_signal,
    capture_inbox_entry,
    gmail_message_already_in_inbox,
)
from app.services.storage_service import create_record, list_records, update_record

logger = logging.getLogger(__name__)

AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"
GMAIL_BASE = "https://gmail.googleapis.com/gmail/v1"
SCOPES = (
    "https://www.googleapis.com/auth/calendar.events "
    "https://www.googleapis.com/auth/gmail.readonly"
)
REQUIRED_CALENDAR_SCOPE = "calendar.events"


def google_has_calendar_write_scope(integration: dict | None) -> bool:
    if not integration or integration.get("status") != "connected":
        return False
    metadata = integration.get("metadata") or {}
    scopes = metadata.get("scopes") or ""
    if isinstance(scopes, list):
        scopes = " ".join(scopes)
    return REQUIRED_CALENDAR_SCOPE in str(scopes)


def google_needs_reconnect(integration: dict | None) -> bool:
    """True when Google is connected but lacks calendar write scope (pre-upgrade tokens)."""
    if not integration or integration.get("status") != "connected":
        return False
    metadata = integration.get("metadata") or {}
    if "scopes" not in metadata:
        return True
    return not google_has_calendar_write_scope(integration)


def _ssl_context() -> ssl.SSLContext:
    """Use certifi CA bundle (macOS Python often lacks system certs for urllib)."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _google_configured() -> bool:
    return bool(
        (os.getenv("GOOGLE_CLIENT_ID") or "").strip()
        and (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()
        and (os.getenv("GOOGLE_REDIRECT_URI") or os.getenv("FRONTEND_URL") or "").strip()
    )


def _redirect_uri() -> str:
    explicit = (os.getenv("GOOGLE_REDIRECT_URI") or "").strip()
    if explicit:
        return explicit.rstrip("/")
    return (
        (os.getenv("FRONTEND_URL") or "http://localhost:3000").rstrip("/")
        + "/integrations/callback"
    )


def _http_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(request, timeout=30, context=_ssl_context()) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Kunne ikke kontakte Google: {exc.reason}") from exc


def _http_get(url: str, access_token: str) -> dict:
    request = urllib.request.Request(url, method="GET")
    request.add_header("Authorization", f"Bearer {access_token}")
    try:
        with urllib.request.urlopen(request, timeout=30, context=_ssl_context()) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Kunne ikke hente fra Google: {exc.reason}") from exc


def _http_json(url: str, access_token: str, payload: dict, *, method: str = "POST") -> dict:
    body = json.dumps(payload).encode()
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Authorization", f"Bearer {access_token}")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=30, context=_ssl_context()) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"Google Calendar feilet ({exc.code}): {detail[:200]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Kunne ikke kontakte Google: {exc.reason}") from exc


def build_google_auth_url(oauth_state: str) -> str:
    params = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "response_type": "code",
        "redirect_uri": _redirect_uri(),
        "scope": SCOPES,
        "state": oauth_state,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }
    return f"{AUTH_BASE}?{urllib.parse.urlencode(params)}"


def exchange_google_code(code: str) -> dict:
    return _http_form(
        TOKEN_URL,
        {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "code": code,
            "redirect_uri": _redirect_uri(),
            "grant_type": "authorization_code",
        },
    )


def refresh_google_token(refresh_token: str) -> dict:
    return _http_form(
        TOKEN_URL,
        {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
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
                tokens = refresh_google_token(refresh)
                access = tokens["access_token"]
                update_record(
                    "user_integrations",
                    integration["id"],
                    {
                        "access_token": access,
                        "refresh_token": tokens.get("refresh_token") or refresh,
                        "token_expires_at": (
                            datetime.now(timezone.utc)
                            + timedelta(seconds=int(tokens.get("expires_in", 3600)))
                        ).isoformat(),
                        "status": "connected",
                    },
                )
        except (urllib.error.URLError, KeyError, ValueError) as exc:
            logger.warning("Google token refresh failed: %s", exc)
            update_record("user_integrations", integration["id"], {"status": "error"})
            return None
    return access


def fetch_calendar_events(access_token: str, days: int = 7, *, max_results: int = 50) -> list[dict]:
    start = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    end = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")
    params = urllib.parse.urlencode(
        {
            "timeMin": start,
            "timeMax": end,
            "maxResults": str(max_results),
            "singleEvents": "true",
            "orderBy": "startTime",
        }
    )
    url = f"{CALENDAR_BASE}/calendars/primary/events?{params}"
    payload = _http_get(url, access_token)
    return payload.get("items") or []


def get_connected_google_integration() -> dict | None:
    return next(
        (
            row
            for row in list_records("user_integrations")
            if row.get("provider") == "google" and row.get("status") == "connected"
        ),
        None,
    )


def get_connected_google_access_token() -> str | None:
    """Return a valid Google access token for the current user's integration."""
    integration = get_connected_google_integration()
    if not integration:
        return None
    return _ensure_access_token(integration)


def _google_datetime(value: datetime, *, all_day: bool = False) -> dict:
    if all_day:
        return {"date": value.astimezone(timezone.utc).strftime("%Y-%m-%d")}
    iso = value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return {"dateTime": iso, "timeZone": "UTC"}


def _parse_google_event_times(event: dict) -> tuple[str, str | None, bool]:
    start = event.get("start") or {}
    end = event.get("end") or {}
    all_day = bool(start.get("date") and not start.get("dateTime"))
    if all_day:
        start_raw = start.get("date")
        start_at = f"{start_raw}T00:00:00+00:00" if start_raw else None
        end_raw = end.get("date")
        end_at = f"{end_raw}T00:00:00+00:00" if end_raw else None
    else:
        start_at = start.get("dateTime")
        end_at = end.get("dateTime")
    return start_at, end_at, all_day


def _calendar_record_from_google(event: dict) -> dict:
    start_at, end_at, all_day = _parse_google_event_times(event)
    return {
        "title": event.get("summary") or "Kalenderhendelse",
        "description": event.get("description"),
        "location": event.get("location"),
        "start_at": start_at,
        "end_at": end_at,
        "all_day": all_day,
        "source": "google",
        "external_id": event.get("id"),
        "calendar_id": "primary",
        "visibility": "household",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def create_google_calendar_event(integration: dict, record: dict) -> dict:
    access = _ensure_access_token(integration)
    if not access:
        raise RuntimeError("Google-token er utløpt.")

    start = datetime.fromisoformat(str(record["start_at"]).replace("Z", "+00:00"))
    end_raw = record.get("end_at")
    end = (
        datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
        if end_raw
        else start + timedelta(hours=1)
    )
    all_day = bool(record.get("all_day"))

    payload = {
        "summary": record.get("title") or "Hendelse",
        "description": record.get("description"),
        "location": record.get("location"),
        "start": _google_datetime(start, all_day=all_day),
        "end": _google_datetime(end, all_day=all_day),
    }
    calendar_id = record.get("calendar_id") or "primary"
    url = f"{CALENDAR_BASE}/calendars/{urllib.parse.quote(calendar_id)}/events"
    return _http_json(url, access, payload, method="POST")


def update_google_calendar_event(integration: dict, record: dict) -> dict:
    access = _ensure_access_token(integration)
    external_id = record.get("external_id")
    if not access or not external_id:
        raise RuntimeError("Mangler Google event ID.")

    start = datetime.fromisoformat(str(record["start_at"]).replace("Z", "+00:00"))
    end_raw = record.get("end_at")
    end = (
        datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
        if end_raw
        else start + timedelta(hours=1)
    )
    all_day = bool(record.get("all_day"))
    calendar_id = record.get("calendar_id") or "primary"

    payload = {
        "summary": record.get("title") or "Hendelse",
        "description": record.get("description"),
        "location": record.get("location"),
        "start": _google_datetime(start, all_day=all_day),
        "end": _google_datetime(end, all_day=all_day),
    }
    url = (
        f"{CALENDAR_BASE}/calendars/{urllib.parse.quote(calendar_id)}"
        f"/events/{urllib.parse.quote(external_id)}"
    )
    return _http_json(url, access, payload, method="PATCH")


def delete_google_calendar_event(
    integration: dict,
    external_id: str,
    *,
    calendar_id: str = "primary",
) -> None:
    access = _ensure_access_token(integration)
    if not access:
        raise RuntimeError("Google-token er utløpt.")
    url = (
        f"{CALENDAR_BASE}/calendars/{urllib.parse.quote(calendar_id)}"
        f"/events/{urllib.parse.quote(external_id)}"
    )
    request = urllib.request.Request(url, method="DELETE")
    request.add_header("Authorization", f"Bearer {access}")
    try:
        with urllib.request.urlopen(request, timeout=30, context=_ssl_context()) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return
        raise RuntimeError(f"Kunne ikke slette Google-hendelse ({exc.code})") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Kunne ikke kontakte Google: {exc.reason}") from exc


def sync_google_calendar_events(integration: dict, *, days: int = 30) -> dict:
    """Upsert Google Calendar events into calendar_events."""
    access = _ensure_access_token(integration)
    if not access:
        raise RuntimeError("Google er ikke tilkoblet eller token er utløpt.")

    google_events = fetch_calendar_events(access, days=days, max_results=100)
    try:
        existing = [
            row
            for row in list_records("calendar_events")
            if row.get("source") == "google" and row.get("external_id")
        ]
    except Exception:
        existing = []
    by_external = {row["external_id"]: row for row in existing}

    created = 0
    updated = 0
    for event in google_events:
        external_id = event.get("id")
        if not external_id:
            continue
        payload = _calendar_record_from_google(event)
        current = by_external.get(external_id)
        if current:
            update_record("calendar_events", current["id"], payload)
            updated += 1
        else:
            create_record("calendar_events", payload)
            created += 1

    update_record(
        "user_integrations",
        integration["id"],
        {"last_sync_at": datetime.now(timezone.utc).isoformat(), "status": "connected"},
    )
    return {
        "provider": "google",
        "synced_events": created + updated,
        "created": created,
        "updated": updated,
    }


def _collect_gmail_attachments(part: dict | None, out: list[dict]) -> None:
    if not part:
        return
    filename = part.get("filename") or ""
    body = part.get("body") or {}
    attachment_id = body.get("attachmentId")
    if filename and attachment_id:
        out.append(
            {
                "filename": filename,
                "attachment_id": attachment_id,
                "mime_type": part.get("mimeType"),
            }
        )
    for child in part.get("parts") or []:
        _collect_gmail_attachments(child, out)


def fetch_gmail_message_details(access_token: str, message_id: str) -> dict:
    url = f"{GMAIL_BASE}/users/me/messages/{urllib.parse.quote(message_id)}?format=full"
    payload = _http_get(url, access_token)
    headers = {
        header.get("name", ""): header.get("value", "")
        for header in payload.get("payload", {}).get("headers") or []
    }
    attachments: list[dict] = []
    _collect_gmail_attachments(payload.get("payload"), attachments)
    return {
        "id": message_id,
        "subject": headers.get("Subject") or "Uten emne",
        "from_address": headers.get("From") or "",
        "snippet": payload.get("snippet") or "",
        "attachments": attachments,
    }


def download_gmail_attachment(access_token: str, message_id: str, attachment_id: str) -> bytes:
    url = (
        f"{GMAIL_BASE}/users/me/messages/{urllib.parse.quote(message_id)}"
        f"/attachments/{urllib.parse.quote(attachment_id)}"
    )
    payload = _http_get(url, access_token)
    encoded = payload.get("data") or ""
    padded = encoded + "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(padded.encode())


def _gmail_subject(access_token: str, message_id: str) -> str:
    url = (
        f"{GMAIL_BASE}/users/me/messages/{urllib.parse.quote(message_id)}"
        "?format=metadata&metadataHeaders=Subject"
    )
    payload = _http_get(url, access_token)
    for header in payload.get("payload", {}).get("headers") or []:
        if header.get("name") == "Subject":
            return header.get("value") or "Uten emne"
    return "Uten emne"


def fetch_unread_emails(access_token: str, limit: int = 8) -> list[dict]:
    list_url = f"{GMAIL_BASE}/users/me/messages?q=is:unread&maxResults={limit}"
    payload = _http_get(list_url, access_token)
    messages = payload.get("messages") or []
    results = []
    for message in messages:
        message_id = message.get("id")
        if not message_id:
            continue
        results.append(fetch_gmail_message_details(access_token, message_id))
    return results


def sync_google_to_inbox(integration: dict) -> dict:
    """Pull unread mail into Inbox and sync calendar into calendar_events."""
    access = _ensure_access_token(integration)
    if not access:
        raise RuntimeError("Google er ikke tilkoblet eller token er utløpt.")

    calendar_result = sync_google_calendar_events(integration, days=30)
    created = 0
    try:
        for message in fetch_unread_emails(access):
            message_id = message.get("id") or ""
            subject = message.get("subject") or "Uten emne"
            if gmail_message_already_in_inbox(message_id, subject=subject):
                continue
            item = capture_google_email_signal(
                subject=subject,
                snippet=message.get("snippet") or "",
                from_address=message.get("from_address") or "",
                gmail_message_id=message_id,
                attachment_meta=message.get("attachments") or [],
            )
            if item is not None:
                created += 1
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Kunne ikke hente fra Google: {exc}") from exc

    update_record(
        "user_integrations",
        integration["id"],
        {"last_sync_at": datetime.now(timezone.utc).isoformat(), "status": "connected"},
    )
    return {
        "synced_signals": created,
        "synced_events": calendar_result.get("synced_events", 0),
        "provider": "google",
    }


def start_google_oauth(user_id: str) -> dict:
    if not _google_configured():
        raise RuntimeError(
            "Google er ikke konfigurert. Sett GOOGLE_CLIENT_ID, "
            "GOOGLE_CLIENT_SECRET og GOOGLE_REDIRECT_URI i .env."
        )
    oauth_state = secrets.token_urlsafe(24)
    existing = next(
        (row for row in list_records("user_integrations") if row.get("provider") == "google"),
        None,
    )
    payload = {
        "provider": "google",
        "status": "pending",
        "metadata": {"oauth_state": oauth_state},
    }
    if existing:
        update_record("user_integrations", existing["id"], payload)
    else:
        create_record("user_integrations", payload)

    return {"auth_url": build_google_auth_url(oauth_state), "configured": True}


def complete_google_oauth(code: str, state: str, user_id: str) -> dict:
    rows = list_records("user_integrations")
    integration = next(
        (
            row
            for row in rows
            if row.get("provider") == "google"
            and (row.get("metadata") or {}).get("oauth_state") == state
            and row.get("user_id") == user_id
        ),
        None,
    )
    if not integration:
        raise RuntimeError("Ugyldig OAuth-state. Prøv å koble til på nytt.")

    tokens = exchange_google_code(code)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(tokens.get("expires_in", 3600)))
    updated = update_record(
        "user_integrations",
        integration["id"],
        {
            "status": "connected",
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "token_expires_at": expires_at.isoformat(),
            "metadata": {
                "scopes": tokens.get("scope") or SCOPES,
                "connected_at": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
    return updated or integration
