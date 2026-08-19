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
    "https://www.googleapis.com/auth/calendar.readonly "
    "https://www.googleapis.com/auth/gmail.readonly"
)


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


def fetch_calendar_events(access_token: str, days: int = 7) -> list[dict]:
    start = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    end = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")
    params = urllib.parse.urlencode(
        {
            "timeMin": start,
            "timeMax": end,
            "maxResults": "15",
            "singleEvents": "true",
            "orderBy": "startTime",
        }
    )
    url = f"{CALENDAR_BASE}/calendars/primary/events?{params}"
    payload = _http_get(url, access_token)
    return payload.get("items") or []


def get_connected_google_access_token() -> str | None:
    """Return a valid Google access token for the current user's integration."""
    integration = next(
        (
            row
            for row in list_records("user_integrations")
            if row.get("provider") == "google" and row.get("status") == "connected"
        ),
        None,
    )
    if not integration:
        return None
    return _ensure_access_token(integration)


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
    """Pull calendar + unread mail into Inbox signals."""
    access = _ensure_access_token(integration)
    if not access:
        raise RuntimeError("Google er ikke tilkoblet eller token er utløpt.")

    created = 0
    try:
        for event in fetch_calendar_events(access):
            title = event.get("summary") or "Kalenderhendelse"
            start_raw = (event.get("start") or {}).get("dateTime") or (event.get("start") or {}).get(
                "date"
            ) or ""
            start = str(start_raw)[:16].replace("T", " ")
            capture_inbox_entry(
                f"Google kalender: {title}" + (f" ({start})" if start else ""),
                fast=True,
            )
            created += 1

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
    return {"synced_signals": created, "provider": "google"}


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
            "metadata": {},
        },
    )
    return updated or integration
