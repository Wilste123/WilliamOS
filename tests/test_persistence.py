"""Tests for durable DB persistence across core modules."""

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_local_store(monkeypatch, tmp_path):
    """Redirect the local JSON store to a temp directory and disable Supabase."""
    from app.services import storage_service
    monkeypatch.setattr(storage_service, "DATA_DIR", tmp_path / ".williamos")
    monkeypatch.setattr(storage_service, "DATA_FILE", tmp_path / ".williamos" / "local_store.json")
    monkeypatch.setattr(storage_service, "get_supabase", lambda: None)


# ---------------------------------------------------------------------------
# 1. create / update roundtrip for each entity
# ---------------------------------------------------------------------------

class TestProjectPersistence:
    def test_create_project_persists(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.services.action_engine import create_project
        from app.services.storage_service import list_records

        project = create_project({"name": "Test Project", "status": "active"})
        assert project.get("id") is not None
        records = list_records("projects")
        assert any(r["id"] == project["id"] for r in records)

    def test_update_project_persists(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.services.action_engine import create_project, update_project
        from app.services.storage_service import get_record

        project = create_project({"name": "Old Name", "status": "active"})
        updated = update_project(project["id"], {"name": "New Name"})
        assert updated is not None
        assert updated["name"] == "New Name"
        stored = get_record("projects", project["id"])
        assert stored["name"] == "New Name"


class TestTaskPersistence:
    def test_create_task_persists(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.services.action_engine import create_task
        from app.services.storage_service import list_records

        task = create_task({"title": "Test Task", "priority": 2, "status": "open"})
        assert task.get("id") is not None
        records = list_records("tasks")
        assert any(r["id"] == task["id"] for r in records)

    def test_update_task_persists_completed(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.services.action_engine import create_task, update_task
        from app.services.storage_service import get_record

        task = create_task({"title": "Todo", "priority": 1, "status": "open"})
        updated = update_task(task["id"], {"completed": True, "status": "completed"})
        assert updated["completed"] is True
        stored = get_record("tasks", task["id"])
        assert stored["completed"] is True


class TestAssetPersistence:
    def test_create_asset_persists(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.services.action_engine import create_asset
        from app.services.storage_service import list_records

        asset = create_asset({"name": "Boat", "type": "båt", "status": "active"})
        assert asset.get("id") is not None
        records = list_records("assets")
        assert any(r["id"] == asset["id"] for r in records)

    def test_update_asset_persists(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.services.action_engine import create_asset, update_asset
        from app.services.storage_service import get_record

        asset = create_asset({"name": "Car", "status": "active"})
        updated = update_asset(asset["id"], {"estimated_value": 250000})
        assert updated["estimated_value"] == 250000
        stored = get_record("assets", asset["id"])
        assert stored["estimated_value"] == 250000


class TestDecisionPersistence:
    def test_create_decision_persists(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.services.action_engine import create_decision
        from app.services.storage_service import list_records

        decision = create_decision({"title": "Buy or rent?", "status": "open"})
        assert decision.get("id") is not None
        records = list_records("decisions")
        assert any(r["id"] == decision["id"] for r in records)

    def test_update_decision_to_decided(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.services.action_engine import create_decision, update_decision
        from app.services.storage_service import get_record

        decision = create_decision({"title": "Buy boat", "status": "open"})
        updated = update_decision(decision["id"], {"status": "decided"})
        assert updated["status"] == "decided"
        assert updated.get("decided_at") is not None
        stored = get_record("decisions", decision["id"])
        assert stored["status"] == "decided"


class TestDocumentPersistence:
    def test_create_document_persists(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.services.action_engine import create_document
        from app.services.storage_service import list_records

        doc = create_document({"filename": "report.pdf", "storage_path": "/uploads/report.pdf"})
        assert doc.get("id") is not None
        records = list_records("documents")
        assert any(r["id"] == doc["id"] for r in records)


# ---------------------------------------------------------------------------
# 2. _execute_tool error propagation — storage failure must surface error
# ---------------------------------------------------------------------------

class TestExecuteToolErrorPropagation:
    def test_update_nonexistent_asset_returns_error(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("update_asset", {"asset_id": "nonexistent-id", "name": "X"})
        assert "error" in result

    def test_update_nonexistent_task_returns_error(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("update_task", {"task_id": "nonexistent-id", "title": "X"})
        assert "error" in result

    def test_update_nonexistent_project_returns_error(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("update_project", {"project_id": "nonexistent-id", "name": "X"})
        assert "error" in result

    def test_update_nonexistent_decision_returns_error(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("update_decision", {"decision_id": "nonexistent-id", "status": "decided"})
        assert "error" in result

    def test_unknown_function_returns_error(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("nonexistent_function", {})
        assert "error" in result

    def test_create_project_via_tool_returns_id(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("create_project", {"name": "Via tool"})
        assert "id" in result
        assert "error" not in result


# ---------------------------------------------------------------------------
# 3. End-to-end: chat action via regex fast path persists to store
# ---------------------------------------------------------------------------

class TestChatActionPersistence:
    def test_create_project_chat_command(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.agents.pa_agent import ask_agent
        from app.services.storage_service import list_records

        answer, _ = ask_agent("lag prosjekt Hytte-renovering", use_documents=False)
        assert "✅" in answer
        projects = list_records("projects")
        assert any("Hytte-renovering" in p.get("name", "") for p in projects)

    def test_create_task_chat_command(self, tmp_path, monkeypatch):
        _patch_local_store(monkeypatch, tmp_path)
        from app.agents.pa_agent import ask_agent
        from app.services.storage_service import list_records

        answer, _ = ask_agent("lag oppgave Bestill materialer", use_documents=False)
        assert "✅" in answer
        tasks = list_records("tasks")
        assert any("Bestill materialer" in t.get("title", "") for t in tasks)


# ---------------------------------------------------------------------------
# 4. Supabase fallback — when Supabase raises, local store is used
# ---------------------------------------------------------------------------

class TestSupabaseFallback:
    def test_create_record_falls_back_on_supabase_error(self, tmp_path, monkeypatch):
        from app.services import storage_service

        monkeypatch.setattr(storage_service, "DATA_DIR", tmp_path / ".williamos")
        monkeypatch.setattr(storage_service, "DATA_FILE", tmp_path / ".williamos" / "local_store.json")

        class _FakeTable:
            def insert(self, _payload):
                raise RuntimeError("Supabase unavailable")

        class _FakeClient:
            def table(self, _name):
                return _FakeTable()

        monkeypatch.setattr(storage_service, "get_supabase", lambda: _FakeClient())

        record = storage_service.create_record("projects", {"name": "Fallback Project", "status": "active"})
        assert record.get("id") is not None
        assert record["name"] == "Fallback Project"

        records = storage_service.list_records("projects")
        assert any(r["id"] == record["id"] for r in records)
