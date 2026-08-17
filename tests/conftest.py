import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.services.auth_context import UserContext, clear_refreshed_tokens, set_current_context


@pytest.fixture(autouse=True)
def reset_auth_context():
    yield
    set_current_context(None)
    clear_refreshed_tokens()


@pytest.fixture
def fake_user_context() -> UserContext:
    return UserContext(
        user_id="user-test",
        email="test@example.com",
        household_id="household-test",
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        display_name="Test User",
    )


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authed_client(fake_user_context, monkeypatch):
    monkeypatch.setattr(
        "app.api.middleware.auth_context.build_context_from_tokens",
        lambda _access, _refresh: fake_user_context,
    )
    test_client = TestClient(
        app,
        headers={
            "Authorization": f"Bearer {fake_user_context.access_token}",
            "X-Refresh-Token": fake_user_context.refresh_token,
        },
    )
    yield test_client
