"""Tests for Priority Engine, goals, document intelligence, and chat actions."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _make_fake_supabase(records_by_collection: dict | None = None):
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
    from app.services.auth_context import UserContext, set_current_context

    client = fake_client if fake_client is not None else _make_fake_supabase()
    set_current_context(
        UserContext(
            user_id="user-test",
            email="test@example.com",
            household_id="household-test",
            access_token="test-access-token",
            refresh_token="test-refresh-token",
        )
    )
    monkeypatch.setattr(storage_service, "get_client", lambda: client)
    return client


class TestPriorityEngine:
    def test_ranks_overdue_task_first(self, monkeypatch):
        _patch_supabase(monkeypatch)
        from app.services.action_engine import build_priority_engine, create_task

        create_task({"title": "Senere", "priority": 1, "status": "open"})
        create_task(
            {
                "title": "Forfalt viktig",
                "priority": 3,
                "status": "open",
                "due_date": "2020-01-01T00:00:00+00:00",
            }
        )
        engine = build_priority_engine()
        assert engine["items"][0]["title"] == "Forfalt viktig"
        assert engine["items"][0]["source_type"] == "task"

    def test_includes_goals_and_inbox(self, monkeypatch):
        store = {"goals": [], "inbox_items": []}
        _patch_supabase(monkeypatch, _make_fake_supabase(store))
        from app.services.action_engine import build_priority_engine, create_goal, capture_inbox_entry

        create_goal({"title": "HouseOS launch", "status": "active", "next_step": "Ship MVP"})
        capture_inbox_entry("Må bestille service på Mazda")
        engine = build_priority_engine(limit=10)
        source_types = {item["source_type"] for item in engine["items"]}
        assert "goal" in source_types
        assert "inbox" in source_types

    def test_malformed_inbox_suggestions_do_not_crash(self, monkeypatch):
        import app.services.action_engine as ae

        def fake_list(collection):
            if collection == "inbox_items":
                return [{"id": "1", "status": "captured", "text": "Må service bil", "suggestions": "bad"}]
            return []

        monkeypatch.setattr(ae, "list_records", fake_list)
        engine = ae.build_priority_engine()
        assert engine["items"] == []


class TestDocumentIntelligence:
    def test_classifies_insurance(self):
        from app.services.document_intelligence import classify_document

        assert classify_document("mazda_forsikring.pdf", "Forsikringsbevis for Mazda 3") == "insurance"

    def test_suggests_asset_link(self, monkeypatch):
        store = {
            "assets": [{"id": "asset-1", "name": "Mazda 3", "status": "active"}],
            "documents": [],
        }
        _patch_supabase(monkeypatch, _make_fake_supabase(store))
        from app.services.document_intelligence import analyze_uploaded_document

        result = analyze_uploaded_document("mazda_forsikring.pdf", "Forsikring for Mazda 3")
        assert result["doc_type"] == "insurance"
        assert result["suggested_asset_id"] == "asset-1"
        assert result["suggestions"]


class TestChatActions:
    def test_extract_proposed_task(self):
        from app.services.chat_actions import extract_proposed_actions

        actions = extract_proposed_actions("Du burde opprette oppgave Mazda etterkontroll før 18.10.")
        assert actions
        assert actions[0]["type"] == "create_task"
        assert "Mazda" in actions[0]["title"]

    def test_tool_result_to_action(self):
        from app.services.chat_actions import tool_result_to_action

        action = tool_result_to_action(
            "create_task",
            {"title": "Test"},
            {"id": "task-1", "title": "Test"},
        )
        assert action
        assert action["status"] == "completed"
        assert action["type"] == "create_task"


class TestGoalsApi:
    def test_create_goal(self, monkeypatch, authed_client):
        _patch_supabase(monkeypatch)
        response = authed_client.post(
            "/goals",
            json={"title": "Launch HouseOS", "next_step": "Finish MVP", "status": "active"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Launch HouseOS"

    def test_priorities_endpoint(self, monkeypatch, authed_client):
        _patch_supabase(monkeypatch)
        response = authed_client.get("/priorities")
        assert response.status_code == 200
        body = response.json()
        assert "items" in body
