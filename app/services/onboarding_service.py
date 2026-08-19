"""Onboarding questionnaire — profile preferences + memory seed for PA context."""

from __future__ import annotations

from app.services.memory_service import save_memory
from app.services.profile_service import get_user_profile, update_assistant_name, update_user_profile

PRIMARY_USE_LABELS = {
    "home": "hjem og vedlikehold",
    "work": "jobb og produktivitet",
    "finance": "økonomi",
    "general": "generell livsstyring",
}

ASSET_LABELS = {
    "bolig": "bolig",
    "hytte": "hytte",
    "båt": "båt",
    "bil": "bil",
    "annet": "annet",
}

VALID_PRIMARY_USE = frozenset(PRIMARY_USE_LABELS)
VALID_ASSETS = frozenset(ASSET_LABELS)


def get_onboarding_state() -> dict:
    """Return current onboarding answers from profile preferences."""
    profile = get_user_profile()
    prefs = profile.get("preferences") or {}
    return {
        "onboarding_completed": bool(prefs.get("onboarding_completed")),
        "assistant_name": profile.get("assistant_name"),
        "primary_use": prefs.get("primary_use"),
        "assets_mentioned": prefs.get("assets_mentioned") or [],
        "focus_now": prefs.get("focus_now"),
    }


def skip_onboarding() -> dict:
    """Mark onboarding complete without collecting answers."""
    profile = update_user_profile(preferences={"onboarding_completed": True})
    return _state_from_profile(profile)


def complete_onboarding(
    *,
    assistant_name: str | None = None,
    primary_use: str | None = None,
    assets_mentioned: list[str] | None = None,
    focus_now: str | None = None,
) -> dict:
    """Save onboarding answers, seed memory, mark complete."""
    prefs: dict = {"onboarding_completed": True}

    if primary_use and primary_use in VALID_PRIMARY_USE:
        prefs["primary_use"] = primary_use

    if assets_mentioned is not None:
        cleaned = [a for a in assets_mentioned if a in VALID_ASSETS]
        prefs["assets_mentioned"] = cleaned

    if focus_now is not None:
        cleaned = focus_now.strip()
        if cleaned:
            prefs["focus_now"] = cleaned[:500]

    if assistant_name and assistant_name.strip():
        update_assistant_name(assistant_name.strip())

    profile = update_user_profile(preferences=prefs)
    seed_onboarding_memory(prefs, profile.get("display_name"))
    return _state_from_profile(profile)


def seed_onboarding_memory(prefs: dict, display_name: str | None = None) -> None:
    """Write durable memory rows from onboarding answers."""
    lines: list[str] = []

    primary = prefs.get("primary_use")
    if primary in PRIMARY_USE_LABELS:
        label = PRIMARY_USE_LABELS[primary]
        lines.append(f"Brukeren vil bruke appen mest til {label}.")

    assets = prefs.get("assets_mentioned") or []
    if assets:
        names = ", ".join(ASSET_LABELS.get(a, a) for a in assets)
        lines.append(f"Brukeren vil holde styr på: {names}.")

    focus = (prefs.get("focus_now") or "").strip()
    if focus:
        lines.append(f"Viktigst for brukeren akkurat nå: {focus}")

    if display_name and display_name.strip():
        lines.append(f"Brukerens navn er {display_name.strip()}.")

    for line in lines:
        save_memory(line, category="profil", source="onboarding")


def build_onboarding_system_block() -> str:
    """Format onboarding preferences as a PA system-message block."""
    try:
        state = get_onboarding_state()
    except Exception:
        return ""

    if not state.get("onboarding_completed"):
        return ""

    parts: list[str] = []
    primary = state.get("primary_use")
    if primary in PRIMARY_USE_LABELS:
        parts.append(f"Hovedfokus: {PRIMARY_USE_LABELS[primary]}.")

    assets = state.get("assets_mentioned") or []
    if assets:
        names = ", ".join(ASSET_LABELS.get(a, a) for a in assets)
        parts.append(f"Eiendeler brukeren bryr seg om: {names}.")

    focus = (state.get("focus_now") or "").strip()
    if focus:
        parts.append(f"Aktuelt fokus: {focus}")

    if not parts:
        return ""

    return "Brukerprofil fra onboarding:\n" + "\n".join(f"- {p}" for p in parts)


def _state_from_profile(profile: dict) -> dict:
    prefs = profile.get("preferences") or {}
    return {
        "onboarding_completed": bool(prefs.get("onboarding_completed")),
        "assistant_name": profile.get("assistant_name"),
        "primary_use": prefs.get("primary_use"),
        "assets_mentioned": prefs.get("assets_mentioned") or [],
        "focus_now": prefs.get("focus_now"),
    }
