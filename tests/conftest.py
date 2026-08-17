import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.main import app
from app.services.auth_context import UserContext, set_current_context


@pytest.fixture
def fake_user_context() -> UserContext:
    return UserContext(
        user_id="00000000-0000-4000-8000-000000000001",
        email="test@example.com",
        household_id="00000000-0000-4000-8000-000000000002",
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        display_name="Test User",
    )


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authed_client(fake_user_context):
    def override_get_current_user():
        set_current_context(fake_user_context)
        try:
            yield fake_user_context
        finally:
            set_current_context(None)

    app.dependency_overrides[get_current_user] = override_get_current_user
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
