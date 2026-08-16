"""Tests for assistant name personalization."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TestBuildSystemPrompt:
    def test_uses_custom_assistant_name(self):
        from app.agents.pa_agent import build_system_prompt

        prompt = build_system_prompt(assistant_name="Jarvis", user_name="William")
        assert "You are Jarvis, William's personal AI assistant." in prompt
        assert "refer to yourself as Jarvis" in prompt

    def test_defaults_when_name_missing(self):
        from app.agents.pa_agent import build_system_prompt

        prompt = build_system_prompt()
        assert "You are WilliamOS, brukeren's personal AI assistant." in prompt
