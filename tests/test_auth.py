"""Tests for app.services.auth_service."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Minimal Supabase Auth stub
# ---------------------------------------------------------------------------

def _make_user(uid: str = "user-abc", email: str = "test@example.com"):
    user = MagicMock()
    user.id = uid
    user.email = email
    return user


def _make_session():
    session = MagicMock()
    session.access_token = "fake-token"
    return session


def _make_auth_response(user=None, session=None):
    resp = MagicMock()
    resp.user = user
    resp.session = session
    return resp


def _make_query_stub(initial_data=None):
    """Return a minimal chained-query stub backed by *initial_data* list."""
    store: list[dict] = list(initial_data) if initial_data else []

    class _Q:
        def __init__(self):
            self._upd = None
            self._single = False
            self._filters: dict = {}

        def select(self, _f="*"):
            return self

        def insert(self, payload):
            store.append(payload)
            return self

        def upsert(self, payload, **_kwargs):
            uid = payload.get("user_id")
            for i, r in enumerate(store):
                if r.get("user_id") == uid:
                    store[i] = {**r, **payload}
                    return self
            store.append(payload)
            return self

        def update(self, payload):
            self._upd = payload
            return self

        def eq(self, field, value):
            self._filters[field] = value
            return self

        def maybe_single(self):
            self._single = True
            return self

        def execute(self):
            if self._upd is not None:
                updated = None
                for i, r in enumerate(store):
                    if all(r.get(k) == v for k, v in self._filters.items()):
                        store[i] = {**r, **self._upd}
                        updated = store[i]
                        break
                return MagicMock(data=[updated] if updated else [])
            # select / insert / upsert
            result = [r for r in store if all(r.get(k) == v for k, v in self._filters.items())]
            if self._single:
                return MagicMock(data=result[0] if result else None)
            return MagicMock(data=result)

    return _Q(), store


def _make_fake_supabase(profile_store=None):
    store = profile_store if profile_store is not None else []
    stub_client = MagicMock()

    def _table(name):
        q, _ = _make_query_stub(store if name == "user_profiles" else [])
        return q

    stub_client.table.side_effect = _table
    return stub_client


# ---------------------------------------------------------------------------
# Tests: register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_register_success(self, monkeypatch):
        from app.services import auth_service

        user = _make_user()
        session = _make_session()
        fake_sb = _make_fake_supabase()
        fake_sb.auth.sign_up.return_value = _make_auth_response(user=user, session=session)
        monkeypatch.setattr(auth_service, "get_supabase", lambda: fake_sb)

        result = auth_service.register(
            "test@example.com", "secret123", name="Alice", age=30, assistant_name="ARIA"
        )
        assert result["user"] is user
        assert result["session"] is session
        fake_sb.auth.sign_up.assert_called_once()

    def test_register_raises_when_no_user_returned(self, monkeypatch):
        from app.services import auth_service

        fake_sb = _make_fake_supabase()
        fake_sb.auth.sign_up.return_value = _make_auth_response(user=None, session=None)
        monkeypatch.setattr(auth_service, "get_supabase", lambda: fake_sb)

        with pytest.raises(RuntimeError, match="Registration failed"):
            auth_service.register("bad@example.com", "pass")

    def test_register_raises_without_supabase(self, monkeypatch):
        from app.services import auth_service
        monkeypatch.setattr(auth_service, "get_supabase", lambda: None)

        with pytest.raises(RuntimeError, match="Supabase is not configured"):
            auth_service.register("x@x.com", "pass")


# ---------------------------------------------------------------------------
# Tests: login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, monkeypatch):
        from app.services import auth_service

        user = _make_user()
        session = _make_session()
        fake_sb = _make_fake_supabase()
        fake_sb.auth.sign_in_with_password.return_value = _make_auth_response(user=user, session=session)
        monkeypatch.setattr(auth_service, "get_supabase", lambda: fake_sb)

        result = auth_service.login("test@example.com", "secret123")
        assert result["user"] is user

    def test_login_fails_with_no_user(self, monkeypatch):
        from app.services import auth_service

        fake_sb = _make_fake_supabase()
        fake_sb.auth.sign_in_with_password.return_value = _make_auth_response(user=None)
        monkeypatch.setattr(auth_service, "get_supabase", lambda: fake_sb)

        with pytest.raises(RuntimeError, match="Login failed"):
            auth_service.login("bad@example.com", "wrong")

    def test_login_raises_without_supabase(self, monkeypatch):
        from app.services import auth_service
        monkeypatch.setattr(auth_service, "get_supabase", lambda: None)

        with pytest.raises(RuntimeError, match="Supabase is not configured"):
            auth_service.login("x@x.com", "pass")


# ---------------------------------------------------------------------------
# Tests: logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout_calls_sign_out(self, monkeypatch):
        from app.services import auth_service

        fake_sb = _make_fake_supabase()
        monkeypatch.setattr(auth_service, "get_supabase", lambda: fake_sb)

        auth_service.logout()
        fake_sb.auth.sign_out.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: user profile
# ---------------------------------------------------------------------------

class TestUserProfile:
    def test_get_profile_returns_row(self, monkeypatch):
        from app.services import auth_service

        profile_data = [{"user_id": "u1", "name": "Alice", "age": 30, "assistant_name": "ARIA"}]
        fake_sb = _make_fake_supabase(profile_store=profile_data)
        monkeypatch.setattr(auth_service, "get_supabase", lambda: fake_sb)

        result = auth_service.get_user_profile("u1")
        assert result is not None
        assert result["name"] == "Alice"

    def test_update_profile(self, monkeypatch):
        from app.services import auth_service

        profile_data = [{"user_id": "u1", "name": "Alice", "age": 30, "assistant_name": "ARIA"}]
        fake_sb = _make_fake_supabase(profile_store=profile_data)
        monkeypatch.setattr(auth_service, "get_supabase", lambda: fake_sb)

        result = auth_service.update_user_profile("u1", {"name": "Bob"})
        assert result is not None
        assert result["name"] == "Bob"


# ---------------------------------------------------------------------------
# Tests: list_records with user_id filter
# ---------------------------------------------------------------------------

class TestListRecordsUserFilter:
    def _make_storage_client(self, store):
        from tests.test_persistence import _make_fake_supabase as _make_sb
        return _make_sb({"assets": store})

    def test_list_records_without_filter_returns_all(self, monkeypatch):
        from app.services import storage_service

        store = [
            {"id": "1", "name": "A", "user_id": "u1", "created_at": "2026-01-01"},
            {"id": "2", "name": "B", "user_id": "u2", "created_at": "2026-01-02"},
        ]
        fake_sb = self._make_storage_client(store)
        monkeypatch.setattr(storage_service, "get_supabase", lambda: fake_sb)

        result = storage_service.list_records("assets")
        assert len(result) == 2

    def test_list_records_with_user_id_filters(self, monkeypatch):
        from app.services import storage_service

        store = [
            {"id": "1", "name": "A", "user_id": "u1", "created_at": "2026-01-01"},
            {"id": "2", "name": "B", "user_id": "u2", "created_at": "2026-01-02"},
        ]
        fake_sb = self._make_storage_client(store)
        monkeypatch.setattr(storage_service, "get_supabase", lambda: fake_sb)

        result = storage_service.list_records("assets", user_id="u1")
        assert len(result) == 1
        assert result[0]["id"] == "1"
