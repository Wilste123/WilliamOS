"""Tests for onboarding service."""

from unittest.mock import patch

import pytest

from app.services.onboarding_service import (
    build_onboarding_system_block,
    complete_onboarding,
    get_onboarding_state,
    skip_onboarding,
)


@pytest.fixture
def mock_profile():
    profile = {
        "user_id": "u1",
        "email": "a@b.no",
        "household_id": "h1",
        "display_name": "William",
        "assistant_name": "Mini-jarv",
        "preferences": {
            "language": "nb",
            "default_asset_type": "other",
            "inbox_automation": True,
            "onboarding_completed": False,
            "primary_use": None,
            "assets_mentioned": [],
            "focus_now": None,
        },
    }

    with patch("app.services.onboarding_service.get_user_profile", return_value=profile):
        with patch("app.services.onboarding_service.update_user_profile", return_value=profile) as upd:
            with patch("app.services.onboarding_service.update_assistant_name", return_value="Mini-jarv"):
                with patch("app.services.onboarding_service.save_memory"):
                    yield profile, upd


def test_get_onboarding_state(mock_profile):
    profile, _ = mock_profile
    state = get_onboarding_state()
    assert state["onboarding_completed"] is False
    assert state["assistant_name"] == "Mini-jarv"


def test_skip_onboarding(mock_profile):
    profile, upd = mock_profile
    profile["preferences"]["onboarding_completed"] = True
    upd.return_value = profile
    state = skip_onboarding()
    assert state["onboarding_completed"] is True
    upd.assert_called_once()


def test_complete_onboarding(mock_profile):
    profile, upd = mock_profile
    profile["preferences"].update(
        {
            "onboarding_completed": True,
            "primary_use": "home",
            "assets_mentioned": ["hytte"],
            "focus_now": "Vinterklargjøring",
        }
    )
    upd.return_value = profile
    state = complete_onboarding(
        assistant_name="Mini-jarv",
        primary_use="home",
        assets_mentioned=["hytte"],
        focus_now="Vinterklargjøring",
    )
    assert state["primary_use"] == "home"
    assert "hytte" in state["assets_mentioned"]


def test_build_onboarding_system_block_incomplete(mock_profile):
    block = build_onboarding_system_block()
    assert block == ""


def test_build_onboarding_system_block_complete(mock_profile):
    profile, _ = mock_profile
    profile["preferences"].update(
        {
            "onboarding_completed": True,
            "primary_use": "home",
            "assets_mentioned": ["hytte", "bil"],
            "focus_now": "Få styr på hytta",
        }
    )
    block = build_onboarding_system_block()
    assert "Brukerprofil fra onboarding" in block
    assert "hytte" in block
    assert "Få styr på hytta" in block
