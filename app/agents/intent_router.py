"""Lightweight intent routing for PA agent context hints."""

from __future__ import annotations

INTENT_HINTS: dict[str, str] = {
    "schedule": (
        "Brukeren spør om kalender/planlegging. "
        "Bruk list_upcoming_schedule først, deretter relevante create/update calendar tools."
    ),
    "documents": (
        "Brukeren spør om dokumenter/forsikring/kontrakter. "
        "Bruk search_documents og workspace-data før web_search."
    ),
    "finance": (
        "Brukeren spør om økonomi/formue. "
        "Bruk get_priority_focus og get_weekly_brief; ikke finans-API ennå."
    ),
    "mission": (
        "Brukeren vil at du skal utføre et multi-step oppdrag. "
        "Kall flere verktøy i rekkefølge og oppsummer hva som foreslås."
    ),
}


def detect_intent(message: str) -> str:
    lowered = (message or "").lower()
    if lowered.startswith("oppdrag") or lowered.startswith("mission"):
        return "mission"
    if any(token in lowered for token in ("kalender", "møte", "avtale", "schedule", "book ")):
        return "schedule"
    if any(
        token in lowered
        for token in ("dokument", "forsikring", "kontrakt", "pdf", "polise", "faktura")
    ):
        return "documents"
    if any(token in lowered for token in ("økonomi", "formue", "net worth", "konto", "bank")):
        return "finance"
    return "general"


def intent_system_hint(message: str) -> str | None:
    intent = detect_intent(message)
    return INTENT_HINTS.get(intent)
