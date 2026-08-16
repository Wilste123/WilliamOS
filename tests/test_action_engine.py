"""Tests for core service logic: capture_inbox_entry and build_dashboard_summary.

These functions contain non-trivial pure-Python logic that runs independently
of Streamlit and should be covered to guard against regressions when
refactoring the UI layer.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Helpers (reused from test_persistence.py pattern)
# ---------------------------------------------------------------------------

def _make_fake_supabase(records_by_collection: dict | None = None):
    """Build a minimal in-memory Supabase stub supporting CRUD."""
    store = records_by_collection if records_by_collection is not None else {}

    class _Query:
        def __init__(self, collection):
            self._collection = collection
            self._filters = {}
            self._op = None
            self._payload = None
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
    from app.services import storage_service
    client = fake_client if fake_client is not None else _make_fake_supabase()
    monkeypatch.setattr(storage_service, "get_client", lambda: client)
    return client


# ---------------------------------------------------------------------------
# capture_inbox_entry — rule-based suggestion logic
# ---------------------------------------------------------------------------

class TestCaptureInboxEntry:
    def test_purchase_intent_generates_asset_and_decision_suggestions(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import capture_inbox_entry

        result = capture_inbox_entry("Vurderer å kjøpe Pioner 320 til 25000")
        assert result["status"] == "captured"
        types = {s["object_type"] for s in result["suggestions"]}
        assert "asset" in types
        assert "decision" in types

    def test_amount_extracted_from_purchase_text(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import capture_inbox_entry

        result = capture_inbox_entry("Kjøpe båt til 150000")
        asset_suggestions = [s for s in result["suggestions"] if s["object_type"] == "asset"]
        assert asset_suggestions
        assert asset_suggestions[0]["fields"]["estimated_value"] == 150000.0

    def test_task_keyword_generates_task_suggestion(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import capture_inbox_entry

        result = capture_inbox_entry("Må bestille service på bilen")
        types = {s["object_type"] for s in result["suggestions"]}
        assert "task" in types

    def test_no_keywords_yields_no_suggestions(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import capture_inbox_entry

        result = capture_inbox_entry("Hei hei")
        assert result["suggestions"] == []

    def test_inbox_item_persisted(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import capture_inbox_entry
        from app.services.storage_service import list_records

        capture_inbox_entry("Test tekst")
        items = list_records("inbox_items")
        assert any(i["text"] == "Test tekst" for i in items)


# ---------------------------------------------------------------------------
# build_dashboard_summary — aggregation logic
# ---------------------------------------------------------------------------

class TestBuildDashboardSummary:
    def _seed_data(self, monkeypatch):
        """Patch Supabase with a pre-seeded store and return it."""
        store = {}
        client = _make_fake_supabase(store)
        _patch_supabase(monkeypatch, client)
        from app.services.action_engine import (
            create_asset,
            create_decision,
            create_project,
            create_task,
        )

        create_asset({"name": "Hytte", "status": "active"})
        create_project({"name": "Renovering", "status": "active"})
        create_task({"title": "Bestill materialer", "priority": 3, "status": "open"})
        create_task({"title": "Ring forsikring", "priority": 2, "status": "completed", "completed": True})
        create_decision({"title": "Kjøp eller leie?", "status": "open"})
        return store

    def test_metrics_counts_are_correct(self, monkeypatch):
        self._seed_data(monkeypatch)
        from app.services.action_engine import build_dashboard_summary

        dash = build_dashboard_summary()
        m = dash["metrics"]
        assert m["assets"] == 1
        assert m["projects"] == 1
        # Only non-completed tasks should be counted
        assert m["open_tasks"] == 1
        assert m["open_decisions"] == 1

    def test_priorities_sorted_by_priority_desc(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import build_dashboard_summary, create_task

        create_task({"title": "Low priority", "priority": 1, "status": "open"})
        create_task({"title": "High priority", "priority": 3, "status": "open"})
        dash = build_dashboard_summary()
        priorities = dash["priorities"]
        assert len(priorities) >= 2
        assert priorities[0]["priority"] == 3
        assert priorities[1]["priority"] == 1

    def test_dashboard_keys_present(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import build_dashboard_summary

        dash = build_dashboard_summary()
        for key in ("metrics", "priorities", "upcoming_events", "active_projects", "new_documents", "recent_activity"):
            assert key in dash

    def test_active_projects_filtered(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import build_dashboard_summary, create_project

        create_project({"name": "Active", "status": "active"})
        create_project({"name": "Done", "status": "done"})
        dash = build_dashboard_summary()
        assert all(p["status"] == "active" for p in dash["active_projects"])


class TestApplyInboxSuggestion:
    def test_apply_asset_suggestion_creates_asset(self, monkeypatch):
        store: dict = {}
        _patch_supabase(monkeypatch, _make_fake_supabase(store))
        from app.services.action_engine import apply_inbox_suggestion, capture_inbox_entry
        from app.services.storage_service import list_records

        inbox_item = capture_inbox_entry("Vurderer å kjøpe Pioner 320 til 25000")
        result = apply_inbox_suggestion(inbox_item["id"], 0)

        assert result["object_type"] == "asset"
        assert list_records("assets")
        updated = next(i for i in list_records("inbox_items") if i["id"] == inbox_item["id"])
        assert updated["status"] in {"partial", "processed"}

    def test_apply_invalid_index_raises(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import apply_inbox_suggestion, capture_inbox_entry

        inbox_item = capture_inbox_entry("Hei hei")
        with pytest.raises(ValueError, match="Ugyldig forslagsindeks"):
            apply_inbox_suggestion(inbox_item["id"], 0)


class TestBuildWeeklyBrief:
    def test_weekly_brief_contains_summary_text(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import build_weekly_brief, create_task

        create_task({"title": "Viktig oppgave", "priority": 3, "status": "open"})
        brief = build_weekly_brief()
        assert "summary_text" in brief
        assert "Viktig oppgave" in brief["summary_text"]
        assert brief["metrics"]["open_tasks"] >= 1
