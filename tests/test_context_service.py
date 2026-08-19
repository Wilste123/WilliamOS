from app.services.context_service import build_agent_context_blocks


def test_build_agent_context_blocks_empty_when_services_fail(monkeypatch):
    monkeypatch.setattr(
        "app.services.context_service.build_priority_engine",
        lambda limit=5: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert build_agent_context_blocks() == []


def test_build_agent_context_blocks_includes_focus_and_schedule(monkeypatch):
    monkeypatch.setattr(
        "app.services.context_service.build_priority_engine",
        lambda limit=5: {
            "items": [{"title": "Bestill olje", "reason": "forfall"}],
        },
    )
    monkeypatch.setattr(
        "app.services.context_service.list_upcoming",
        lambda days=14, limit=5: [
            {"title": "Tannlege", "start_at": "2026-08-21T10:00:00", "source": "internal"},
        ],
    )
    monkeypatch.setattr(
        "app.services.context_service.build_timeline",
        lambda limit=5: [{"title": "Opprettet oppgave", "event_type": "task"}],
    )

    blocks = build_agent_context_blocks()

    assert len(blocks) == 3
    assert "Prioritert fokus" in blocks[0]
    assert "Bestill olje" in blocks[0]
    assert "Kommende kalender" in blocks[1]
    assert "Tannlege" in blocks[1]
    assert "Nylig aktivitet" in blocks[2]
