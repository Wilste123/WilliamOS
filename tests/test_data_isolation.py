"""Tests for storage_service auth scoping."""

import pytest

from app.services.auth_context import UserContext, set_current_context


@pytest.fixture
def user_context():
    ctx = UserContext(
        user_id="11111111-1111-4111-8111-111111111111",
        email="a@test.com",
        household_id="22222222-2222-4222-8222-222222222222",
        access_token="access",
        refresh_token="refresh",
        display_name="A",
    )
    set_current_context(ctx)
    yield ctx
    set_current_context(None)


def test_apply_auth_fields_forces_household(user_context):
    from app.services.storage_service import _apply_auth_fields

    record = _apply_auth_fields(
        "tasks",
        {
            "title": "Test",
            "user_id": "evil-user",
            "household_id": "evil-household",
        },
    )
    assert record["user_id"] == user_context.user_id
    assert record["household_id"] == user_context.household_id
    assert record["visibility"] == "household"


def test_apply_auth_fields_private_strips_household(user_context):
    from app.services.storage_service import _apply_auth_fields

    record = _apply_auth_fields("inbox_items", {"text": "note", "visibility": "private"})
    assert record["user_id"] == user_context.user_id
    assert record["household_id"] is None
    assert record["visibility"] == "private"


def test_apply_auth_fields_user_integrations(user_context):
    from app.services.storage_service import _apply_auth_fields

    record = _apply_auth_fields(
        "user_integrations",
        {"provider": "outlook", "visibility": "household", "household_id": "x"},
    )
    assert record["user_id"] == user_context.user_id
    assert "household_id" not in record
    assert "visibility" not in record


def test_sanitize_update_patch():
    from app.services.storage_service import _sanitize_update_patch

    patch = _sanitize_update_patch(
        {"title": "ok", "user_id": "evil", "household_id": "evil", "visibility": "household"}
    )
    assert patch == {"title": "ok"}


def test_get_client_requires_context():
    from app.services.storage_service import get_client

    set_current_context(None)
    with pytest.raises(RuntimeError, match="Authentication required"):
        get_client()


def test_get_client_requires_tokens():
    from app.services.storage_service import get_client

    set_current_context(
        UserContext(
            user_id="11111111-1111-4111-8111-111111111111",
            email="a@test.com",
            household_id="22222222-2222-4222-8222-222222222222",
            access_token="",
            refresh_token="refresh",
        )
    )
    with pytest.raises(RuntimeError, match="Missing session tokens"):
        get_client()
    set_current_context(None)
