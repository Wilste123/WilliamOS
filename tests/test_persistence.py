"""Tests for durable DB persistence across core modules."""

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_supabase(records_by_collection: dict | None = None):
    """Build a minimal in-memory Supabase stub that supports CRUD."""
    store = records_by_collection if records_by_collection is not None else {}

    class _Query:
        def __init__(self, collection):
            self._collection = collection
            self._filters = {}
            self._op = None
            self._payload = None
            self._order_col = None
            self._order_desc = False
            self._single = False

        def select(self, _fields="*"):
            self._op = "select"
            return self

        def insert(self, payload):
            self._op = "insert"
            self._payload = payload
            return self

        def update(self, payload):
            self._op = "update"
            self._payload = payload
            return self

        def eq(self, field, value):
            self._filters[field] = value
            return self

        def order(self, _col, desc=False):
            self._order_desc = desc
            return self

        def limit(self, _count):
            return self

        def maybe_single(self):
            self._single = True
            return self

        def execute(self):
            col = self._collection
            rows = store.setdefault(col, [])
            if self._op == "select":
                result = [r for r in rows if all(r.get(k) == v for k, v in self._filters.items())]
                if self._order_desc:
                    result = sorted(result, key=lambda r: r.get("created_at", ""), reverse=True)
                data = result[0] if self._single and result else (None if self._single else result)
                return type("R", (), {"data": data})()
            if self._op == "insert":
                store[col].append(self._payload)
                return type("R", (), {"data": [self._payload]})()
            if self._op == "update":
                updated = None
                for i, r in enumerate(rows):
                    if all(r.get(k) == v for k, v in self._filters.items()):
                        rows[i] = {**r, **self._payload}
                        updated = rows[i]
                        break
                return type("R", (), {"data": [updated] if updated else []})()
            return type("R", (), {"data": []})()

    class _FakeClient:
        def table(self, name):
            return _Query(name)

    return _FakeClient()


def _patch_supabase(monkeypatch, fake_client=None):
    """Patch get_client to return *fake_client* (or a fresh stub if not given)."""
    from app.services import storage_service
    client = fake_client if fake_client is not None else _make_fake_supabase()
    monkeypatch.setattr(storage_service, "get_client", lambda: client)
    return client


# ---------------------------------------------------------------------------
# 1. create / update roundtrip for each entity
# ---------------------------------------------------------------------------

class TestProjectPersistence:
    def test_create_project_persists(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import create_project
        from app.services.storage_service import list_records

        project = create_project({"name": "Test Project", "status": "active"})
        assert project.get("id") is not None
        records = list_records("projects")
        assert any(r["id"] == project["id"] for r in records)

    def test_update_project_persists(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import create_project, update_project
        from app.services.storage_service import get_record

        project = create_project({"name": "Old Name", "status": "active"})
        updated = update_project(project["id"], {"name": "New Name"})
        assert updated is not None
        assert updated["name"] == "New Name"
        stored = get_record("projects", project["id"])
        assert stored["name"] == "New Name"


class TestTaskPersistence:
    def test_create_task_persists(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import create_task
        from app.services.storage_service import list_records

        task = create_task({"title": "Test Task", "priority": 2, "status": "open"})
        assert task.get("id") is not None
        records = list_records("tasks")
        assert any(r["id"] == task["id"] for r in records)

    def test_update_task_persists_completed(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import create_task, update_task
        from app.services.storage_service import get_record

        task = create_task({"title": "Todo", "priority": 1, "status": "open"})
        updated = update_task(task["id"], {"completed": True, "status": "completed"})
        assert updated["completed"] is True
        stored = get_record("tasks", task["id"])
        assert stored["completed"] is True


class TestAssetPersistence:
    def test_create_asset_persists(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import create_asset
        from app.services.storage_service import list_records

        asset = create_asset({"name": "Boat", "type": "båt", "status": "active"})
        assert asset.get("id") is not None
        records = list_records("assets")
        assert any(r["id"] == asset["id"] for r in records)

    def test_update_asset_persists(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import create_asset, update_asset
        from app.services.storage_service import get_record

        asset = create_asset({"name": "Car", "status": "active"})
        updated = update_asset(asset["id"], {"estimated_value": 250000})
        assert updated["estimated_value"] == 250000
        stored = get_record("assets", asset["id"])
        assert stored["estimated_value"] == 250000


class TestDecisionPersistence:
    def test_create_decision_persists(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import create_decision
        from app.services.storage_service import list_records

        decision = create_decision({"title": "Buy or rent?", "status": "open"})
        assert decision.get("id") is not None
        records = list_records("decisions")
        assert any(r["id"] == decision["id"] for r in records)

    def test_update_decision_to_decided(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import create_decision, update_decision
        from app.services.storage_service import get_record

        decision = create_decision({"title": "Buy boat", "status": "open"})
        updated = update_decision(decision["id"], {"status": "decided"})
        assert updated["status"] == "decided"
        assert updated.get("decided_at") is not None
        stored = get_record("decisions", decision["id"])
        assert stored["status"] == "decided"


class TestDocumentPersistence:
    def test_create_document_persists(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import create_document
        from app.services.storage_service import list_records

        doc = create_document({"filename": "report.pdf", "storage_path": "documents/report.pdf"})
        assert doc.get("id") is not None
        records = list_records("documents")
        assert any(r["id"] == doc["id"] for r in records)


# ---------------------------------------------------------------------------
# 2. _execute_tool error propagation — storage failure must surface error
# ---------------------------------------------------------------------------

class TestExecuteToolErrorPropagation:
    def test_update_nonexistent_asset_returns_error(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("update_asset", {"asset_id": "nonexistent-id", "name": "X"})
        assert "error" in result

    def test_update_nonexistent_task_returns_error(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("update_task", {"task_id": "nonexistent-id", "title": "X"})
        assert "error" in result

    def test_update_nonexistent_project_returns_error(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("update_project", {"project_id": "nonexistent-id", "name": "X"})
        assert "error" in result

    def test_update_nonexistent_decision_returns_error(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("update_decision", {"decision_id": "nonexistent-id", "status": "decided"})
        assert "error" in result

    def test_unknown_function_returns_error(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("nonexistent_function", {})
        assert "error" in result

    def test_create_project_via_tool_returns_id(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("create_project", {"name": "Via tool"})
        assert "id" in result
        assert "error" not in result


# ---------------------------------------------------------------------------
# 3. End-to-end: chat action via regex fast path persists to store
# ---------------------------------------------------------------------------

class TestChatActionPersistence:
    def test_create_project_chat_command(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.agents.pa_agent import ask_agent
        from app.services.storage_service import list_records

        answer, _ = ask_agent("lag prosjekt Hytte-renovering", use_documents=False)
        assert "✅" in answer
        projects = list_records("projects")
        assert any("Hytte-renovering" in p.get("name", "") for p in projects)

    def test_create_task_chat_command(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.agents.pa_agent import ask_agent
        from app.services.storage_service import list_records

        answer, _ = ask_agent("lag oppgave Bestill materialer", use_documents=False)
        assert "✅" in answer
        tasks = list_records("tasks")
        assert any("Bestill materialer" in t.get("title", "") for t in tasks)


# ---------------------------------------------------------------------------
# 4. Supabase-only enforcement — operations must raise when Supabase is absent
# ---------------------------------------------------------------------------

class TestSupabaseRequired:
    def test_list_records_raises_when_supabase_not_configured(self, monkeypatch):
        from app.services import storage_service
        monkeypatch.setattr(storage_service, "get_client", lambda: None)

        with pytest.raises(RuntimeError, match="Supabase is not configured"):
            storage_service.list_records("assets")

    def test_get_record_raises_when_supabase_not_configured(self, monkeypatch):
        from app.services import storage_service
        monkeypatch.setattr(storage_service, "get_client", lambda: None)

        with pytest.raises(RuntimeError, match="Supabase is not configured"):
            storage_service.get_record("assets", "some-id")

    def test_create_record_raises_when_supabase_not_configured(self, monkeypatch):
        from app.services import storage_service
        monkeypatch.setattr(storage_service, "get_client", lambda: None)

        with pytest.raises(RuntimeError, match="Supabase is not configured"):
            storage_service.create_record("projects", {"name": "Test"})

    def test_update_record_raises_when_supabase_not_configured(self, monkeypatch):
        from app.services import storage_service
        monkeypatch.setattr(storage_service, "get_client", lambda: None)

        with pytest.raises(RuntimeError, match="Supabase is not configured"):
            storage_service.update_record("projects", "some-id", {"name": "X"})

    def test_create_record_propagates_supabase_error(self, monkeypatch):
        from app.services import storage_service

        class _BrokenTable:
            def insert(self, _payload):
                raise RuntimeError("DB connection refused")

        class _BrokenClient:
            def table(self, _name):
                return _BrokenTable()

        monkeypatch.setattr(storage_service, "get_client", lambda: _BrokenClient())

        with pytest.raises(RuntimeError, match="DB connection refused"):
            storage_service.create_record("projects", {"name": "Will fail"})

    def test_list_records_propagates_supabase_error(self, monkeypatch):
        from app.services import storage_service

        class _BrokenQuery:
            def select(self, _f="*"):
                return self
            def order(self, _c, desc=False):
                return self
            def execute(self):
                raise RuntimeError("timeout")

        class _BrokenClient:
            def table(self, _name):
                return _BrokenQuery()

        monkeypatch.setattr(storage_service, "get_client", lambda: _BrokenClient())

        with pytest.raises(RuntimeError, match="timeout"):
            storage_service.list_records("assets")
