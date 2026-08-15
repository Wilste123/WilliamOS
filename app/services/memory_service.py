from app.services.storage_service import create_record, list_records

LOCAL_MEMORY = [
    "WilliamOS er første prototype for HouseOS, LifeOS og self-evolve.",
    "Første mål er en mini-Jarvis som brukes daglig.",
]


def get_recent_memory_text(limit: int = 20) -> str:
    """Fetches memory from storage when available. Falls back to local starter memory."""
    try:
        rows = list_records("memory_items")[:limit]
        return "\n".join(f"- {r['value']}" for r in rows)
    except Exception:
        return "\n".join(f"- {m}" for m in LOCAL_MEMORY)


def save_memory(value: str, key: str | None = None, category: str | None = None) -> dict:
    try:
        row = create_record("memory_items", {"value": value, "key": key, "category": category})
        return {"saved": True, "mode": "supabase", "data": row}
    except Exception:
        LOCAL_MEMORY.append(value)
        return {"saved": True, "mode": "local", "value": value}
