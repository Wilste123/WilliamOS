from app.services.google_service import google_has_calendar_write_scope, google_needs_reconnect


def test_google_needs_reconnect_when_scopes_missing():
    row = {"status": "connected", "metadata": {}}
    assert google_needs_reconnect(row) is True


def test_google_needs_reconnect_when_readonly_scope_only():
    row = {
        "status": "connected",
        "metadata": {"scopes": "https://www.googleapis.com/auth/calendar.readonly gmail.readonly"},
    }
    assert google_has_calendar_write_scope(row) is False
    assert google_needs_reconnect(row) is True


def test_google_ok_with_calendar_events_scope():
    row = {
        "status": "connected",
        "metadata": {
            "scopes": (
                "https://www.googleapis.com/auth/calendar.events "
                "https://www.googleapis.com/auth/gmail.readonly"
            )
        },
    }
    assert google_has_calendar_write_scope(row) is True
    assert google_needs_reconnect(row) is False


def test_disconnected_google_does_not_need_reconnect():
    assert google_needs_reconnect({"status": "disconnected"}) is False
    assert google_needs_reconnect(None) is False


def test_list_integration_statuses_flags_reconnect(monkeypatch):
    from app.services import integration_service

    monkeypatch.setattr(
        integration_service,
        "_user_integrations",
        lambda: [{"provider": "google", "status": "connected", "metadata": {}}],
    )
    monkeypatch.setattr(integration_service, "_google_configured", lambda: True)

    statuses = integration_service.list_integration_statuses()
    google = next(item for item in statuses if item["provider"] == "google")
    assert google["needs_reconnect"] is True
