"""Goal module constants for cross-module linking."""

GOAL_MODULES = frozenset({"health", "finance", "asset", "project", "general"})

GOAL_MODULE_LABELS = {
    "health": "Helse",
    "finance": "Økonomi",
    "asset": "Eiendel",
    "project": "Prosjekt",
    "general": "Generelt",
}

MODULE_ENTITY_COLLECTIONS = {
    "health": None,
    "finance": "finance_accounts",
    "asset": "assets",
    "project": "projects",
    "general": None,
}
