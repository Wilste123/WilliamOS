from app.services.storage_service import create_record, list_records


def get_recent_memory_text(limit: int = 20) -> str:
    """Fetch recent memory items from Supabase."""
    rows = list_records("memory_items")[:limit]
    if not rows:
        return "Ingen lagret minne ennå."
    return "\n".join(f"- {r['value']}" for r in rows)


def save_memory(value: str, key: str | None = None, category: str | None = None, visibility: str = "private") -> dict:
    """Persist a memory item to Supabase."""
    record = create_record(
        "memory_items",
        {"value": value, "key": key, "category": category, "visibility": visibility},
    )
    return {"saved": True, "data": record}
