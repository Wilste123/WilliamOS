"""Tests for calendar_events service."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_persistence import _make_fake_supabase, _patch_supabase


def test_create_and_list_calendar_event(monkeypatch):
    _patch_supabase(monkeypatch)
    from app.services.calendar_service import create_calendar_event, list_upcoming

    start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    record = create_calendar_event(
        {
            "title": "Møte med rørlegger",
            "start_at": start,
            "end_at": (datetime.now(timezone.utc) + timedelta(days=1, hours=1)).isoformat(),
        },
        sync_google=False,
    )
    assert record["title"] == "Møte med rørlegger"
    upcoming = list_upcoming(days=7)
    assert any(row["id"] == record["id"] for row in upcoming)


def test_sync_google_calendar_upserts(monkeypatch):
    store = {"calendar_events": [], "user_integrations": []}
    _patch_supabase(monkeypatch, _make_fake_supabase(store))
    from app.services import calendar_service
    from app.services.google_service import sync_google_calendar_events

    integration = {
        "id": "int-1",
        "provider": "google",
        "status": "connected",
        "access_token": "token",
        "refresh_token": "refresh",
    }
    store["user_integrations"].append(integration)

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    google_event = {
        "id": "google-event-1",
        "summary": "Teams standup",
        "start": {"dateTime": tomorrow},
        "end": {"dateTime": tomorrow},
    }

    monkeypatch.setattr(
        "app.services.google_service.fetch_calendar_events",
        lambda access_token, days=7, max_results=50: [google_event],
    )
    monkeypatch.setattr(
        "app.services.google_service._ensure_access_token",
        lambda integration: "token",
    )

    result = sync_google_calendar_events(integration, days=7)
    assert result["created"] == 1
    assert len(store["calendar_events"]) == 1
    assert store["calendar_events"][0]["external_id"] == "google-event-1"

    result2 = sync_google_calendar_events(integration, days=7)
    assert result2["updated"] == 1
    assert result2["created"] == 0


def test_create_calendar_event_pushes_to_google(monkeypatch):
    store = {"calendar_events": [], "user_integrations": []}
    _patch_supabase(monkeypatch, _make_fake_supabase(store))
    from app.services.calendar_service import create_calendar_event

    integration = {
        "id": "int-1",
        "provider": "google",
        "status": "connected",
        "user_id": "00000000-0000-4000-8000-000000000001",
        "access_token": "token",
        "refresh_token": "refresh",
        "metadata": {
            "scopes": "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/gmail.readonly"
        },
    }
    store["user_integrations"].append(integration)

    monkeypatch.setattr(
        "app.services.calendar_service.create_google_calendar_event",
        lambda _integration, record: {"id": "google-new-1", "organizer": {"email": "primary"}},
    )
    monkeypatch.setattr(
        "app.services.calendar_service._ensure_access_token",
        lambda _integration: "token",
    )
    monkeypatch.setattr(
        "app.services.google_service.fetch_token_scopes",
        lambda _token: "https://www.googleapis.com/auth/calendar.events",
    )
    monkeypatch.setattr(
        "app.services.calendar_service._backfill_integration_scopes",
        lambda _integration, _token: None,
    )

    start = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    record = create_calendar_event(
        {"title": "App møte", "start_at": start},
        sync_google=True,
    )
    assert record["google_synced"] is True
    assert record["external_id"] == "google-new-1"


def test_create_calendar_event_reports_missing_write_scope(monkeypatch):
    store = {"calendar_events": [], "user_integrations": []}
    _patch_supabase(monkeypatch, _make_fake_supabase(store))
    from app.services.calendar_service import create_calendar_event

    store["user_integrations"].append(
        {
            "id": "int-1",
            "provider": "google",
            "status": "connected",
            "user_id": "00000000-0000-4000-8000-000000000001",
            "access_token": "token",
            "refresh_token": "refresh",
            "metadata": {"scopes": "https://www.googleapis.com/auth/calendar.readonly"},
        }
    )

    monkeypatch.setattr(
        "app.services.calendar_service._ensure_access_token",
        lambda _integration: "token",
    )
    monkeypatch.setattr(
        "app.services.google_service.fetch_token_scopes",
        lambda _token: "https://www.googleapis.com/auth/calendar.readonly",
    )

    start = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    record = create_calendar_event(
        {"title": "App møte", "start_at": start},
        sync_google=True,
    )
    assert record["google_synced"] is False
    assert "skrivetilgang" in str(record.get("google_sync_error", "")).lower()


def test_list_calendar_events_includes_earlier_today(monkeypatch):
    _patch_supabase(monkeypatch)
    from app.services.calendar_service import create_calendar_event, list_calendar_events

    now = datetime.now(timezone.utc)
    morning = now.replace(hour=9, minute=0, second=0, microsecond=0)
    record = create_calendar_event(
        {"title": "I dag morges", "start_at": morning.isoformat()},
        sync_google=False,
    )
    listed = list_calendar_events(days=7)
    assert any(row["id"] == record["id"] for row in listed)
