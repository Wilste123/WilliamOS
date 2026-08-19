"""Tests for proposal mode, action executor, brief and mission services."""

from __future__ import annotations


class TestProposalPipeline:
    def test_build_proposal_status(self):
        from app.services.chat_actions import build_proposal

        proposal = build_proposal("create_task", {"title": "Ring rørlegger"})
        assert proposal["status"] == "proposed"
        assert proposal["tool"] == "create_task"
        assert proposal["title"] == "Ring rørlegger"

    def test_propose_tool_blocks_execution(self, monkeypatch):
        from tests.test_persistence import _patch_supabase

        _patch_supabase(monkeypatch)
        from app.agents.pa_agent import _execute_tool

        result = _execute_tool("create_task", {"title": "Venter på godkjenning"})
        assert result["status"] == "proposed"

    def test_execute_chat_action_create_task(self, monkeypatch):
        from tests.test_persistence import _patch_supabase

        _patch_supabase(monkeypatch)
        from app.services.action_executor import execute_chat_action

        created = execute_chat_action(
            {
                "tool": "create_task",
                "type": "create_task",
                "payload": {"title": "Fra proposal", "priority": 2, "status": "open"},
            }
        )
        assert created.get("title") == "Fra proposal"
        assert created.get("id")


class TestMissionPlanner:
    def test_plan_mission_hytte(self):
        from app.services.mission_service import plan_mission

        mission = plan_mission("Oppdrag: Forbered hyttetur neste helg")
        assert mission["proposals"]
        assert any("pakkeliste" in p["title"].lower() for p in mission["proposals"])

    def test_handle_actions_mission_fast_path(self, monkeypatch):
        from tests.test_persistence import _patch_supabase

        _patch_supabase(monkeypatch)
        from app.agents.pa_agent import handle_actions

        result = handle_actions("oppdrag: Håndter forsikring for hytta")
        assert result["handled"] is True
        assert result["actions"]
        assert "forsikring" in result["response"].lower() or any(
            "forsikring" in a.get("title", "").lower() for a in result["actions"]
        )


class TestDailyBrief:
    def test_build_daily_brief_shape(self, monkeypatch):
        from tests.test_persistence import _patch_supabase

        _patch_supabase(monkeypatch)
        from app.services.brief_service import build_daily_brief

        brief = build_daily_brief()
        assert "headline" in brief
        assert "proposals" in brief
        assert isinstance(brief["proposals"], list)


class TestIntentRouter:
    def test_detect_schedule_intent(self):
        from app.agents.intent_router import detect_intent

        assert detect_intent("Hva har jeg på kalenderen?") == "schedule"

    def test_detect_mission_intent(self):
        from app.agents.intent_router import detect_intent

        assert detect_intent("oppdrag: forbered hytta") == "mission"


class TestHybridRetrieval:
    def test_keyword_fallback_without_embeddings(self, monkeypatch):
        docs = [{"id": "d1", "filename": "forsikring.pdf", "text_content": "tak hytte"}]
        monkeypatch.setattr("app.services.retrieval_service.list_records", lambda _c: docs)
        monkeypatch.setattr("app.services.embedding_service.embeddings_enabled", lambda: False)
        from app.services.retrieval_service import search_documents

        hits = search_documents("hytte tak")
        assert hits
        assert hits[0]["filename"] == "forsikring.pdf"
