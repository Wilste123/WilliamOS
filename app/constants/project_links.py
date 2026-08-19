"""Project link entity types."""

PROJECT_LINK_TYPES = frozenset(
    {"asset", "goal", "document", "finance_account", "task", "decision"}
)

PROJECT_LINK_LABELS = {
    "asset": "Eiendel",
    "goal": "Mål",
    "document": "Dokument",
    "finance_account": "Finanskonto",
    "task": "Oppgave",
    "decision": "Beslutning",
}

ENTITY_COLLECTIONS = {
    "asset": "assets",
    "goal": "goals",
    "document": "documents",
    "finance_account": "finance_accounts",
    "task": "tasks",
    "decision": "decisions",
}

ENTITY_DETAIL_PATHS = {
    "asset": "/assets/{id}",
    "goal": "/goals/{id}",
    "document": "/documents",
    "finance_account": "/finance",
    "task": "/tasks",
    "decision": "/decisions",
}
