from app.services.google_service import google_has_calendar_write_scope, google_needs_reconnect


def test_google_needs_reconnect_when_scopes_missing(monkeypatch):
    monkeypatch.setattr(
        "app.services.google_service.fetch_token_scopes",
        lambda _token: "",
    )
    row = {"status": "connected", "metadata": {}, "access_token": "tok"}
    assert google_needs_reconnect(row) is True


def test_google_has_write_scope_from_live_token_when_metadata_empty(monkeypatch):
    monkeypatch.setattr(
        "app.services.google_service.fetch_token_scopes",
        lambda _token: "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/gmail.readonly",
    )
    row = {"status": "connected", "metadata": {}, "access_token": "tok"}
    assert google_has_calendar_write_scope(row, access_token="tok") is True
    assert google_needs_reconnect(row) is False


def test_google_needs_reconnect_when_readonly_scope_only(monkeypatch):
    monkeypatch.setattr(
        "app.services.google_service.fetch_token_scopes",
        lambda _token: "https://www.googleapis.com/auth/calendar.readonly",
    )
    row = {
        "status": "connected",
        "access_token": "tok",
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
        lambda: [
            {
                "provider": "google",
                "status": "connected",
                "metadata": {},
                "access_token": "tok",
            }
        ],
    )
    monkeypatch.setattr(integration_service, "_google_configured", lambda: True)
    monkeypatch.setattr(
        "app.services.google_service.fetch_token_scopes",
        lambda _token: "",
    )

    statuses = integration_service.list_integration_statuses()
    google = next(item for item in statuses if item["provider"] == "google")
    assert google["needs_reconnect"] is True
