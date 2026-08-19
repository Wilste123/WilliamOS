"""Tests for Phase 4/5: project links, goal modules, auto-memory."""

from __future__ import annotations


def _make_store() -> dict[str, list[dict]]:
    return {
        "projects": [],
        "project_links": [],
        "goals": [],
        "assets": [],
        "tasks": [],
        "memory_items": [],
        "events": [],
        "finance_accounts": [],
    }


def _install_storage(monkeypatch, store: dict[str, list[dict]]):
    from tests.test_gap_chart_features import _make_fake_supabase, _patch_supabase

    _patch_supabase(monkeypatch, _make_fake_supabase(store))


class TestProjectLinks:
    def test_link_and_detail(self, monkeypatch):
        store = _make_store()
        _install_storage(monkeypatch, store)

        from app.services.action_engine import create_project, get_project_detail, link_to_project
        from app.services.storage_service import create_record

        project = create_project({"name": "Renovering", "status": "active"})
        goal = create_record("goals", {"title": "Ferdigstille bad", "status": "active"})
        link_to_project(project["id"], "goal", goal["id"])

        detail = get_project_detail(project["id"])
        assert detail is not None
        assert len(detail["goals"]) == 1
        assert detail["goals"][0]["title"] == "Ferdigstille bad"
        assert len(detail["links"]) == 1
        assert detail["links"][0]["label"] == "Ferdigstille bad"

    def test_link_is_idempotent(self, monkeypatch):
        store = _make_store()
        _install_storage(monkeypatch, store)

        from app.services.action_engine import create_project, link_to_project
        from app.services.storage_service import create_record, list_records

        project = create_project({"name": "Test", "status": "active"})
        task = create_record("tasks", {"title": "Gjøre noe", "status": "open", "completed": False})
        link1 = link_to_project(project["id"], "task", task["id"])
        link2 = link_to_project(project["id"], "task", task["id"])
        assert link1["id"] == link2["id"]
        assert len(list_records("project_links")) == 1


class TestGoalModules:
    def test_goal_detail_with_linked_asset(self, monkeypatch):
        store = _make_store()
        _install_storage(monkeypatch, store)

        from app.services.action_engine import create_goal, get_goal_detail
        from app.services.storage_service import create_record

        asset = create_record("assets", {"name": "Mazda CX-5", "status": "active", "type": "vehicle"})
        goal = create_goal(
            {
                "title": "Service Mazda",
                "status": "active",
                "module": "asset",
                "linked_id": asset["id"],
            }
        )
        detail = get_goal_detail(goal["id"])
        assert detail is not None
        assert detail["linked_record"]["name"] == "Mazda CX-5"


class TestAutoMemory:
    def test_append_memory_from_asset_created(self, monkeypatch):
        store = _make_store()
        _install_storage(monkeypatch, store)

        from app.services.action_engine import create_asset
        from app.services.storage_service import list_records

        create_asset({"name": "Hytte Tun32", "status": "active", "type": "cabin"})
        memory = list_records("memory_items")
        assert len(memory) == 1
        assert "Hytte Tun32" in memory[0]["value"]
        assert memory[0]["source"] == "asset_created"

    def test_skip_duplicate_memory(self, monkeypatch):
        store = _make_store()
        _install_storage(monkeypatch, store)

        from app.services.memory_service import append_memory_from_event, save_memory
        from app.services.storage_service import list_records

        save_memory("Test minne", source="manual")
        append_memory_from_event("asset_created", "Test minne")
        assert len(list_records("memory_items")) == 1
