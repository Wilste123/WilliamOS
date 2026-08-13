from app.database.supabase import get_supabase

LOCAL_MEMORY = [
    "WilliamOS er første prototype for HouseOS, LifeOS og self-evolve.",
    "Første mål er en mini-Jarvis som brukes daglig.",
]


def get_recent_memory_text(limit: int = 20) -> str:
    """Fetches memory from Supabase if configured. Falls back to local starter memory."""
    supabase = get_supabase()
    if supabase is None:
        return "\n".join(f"- {m}" for m in LOCAL_MEMORY)
    try:
        rows = supabase.table("memory_items").select("value").limit(limit).execute().data
        return "\n".join(f"- {r['value']}" for r in rows)
    except Exception:
        return "\n".join(f"- {m}" for m in LOCAL_MEMORY)


def save_memory(value: str, key: str | None = None, category: str | None = None) -> dict:
    supabase = get_supabase()
    if supabase is None:
        LOCAL_MEMORY.append(value)
        return {"saved": True, "mode": "local", "value": value}
    payload = {"value": value, "key": key, "category": category}
    result = supabase.table("memory_items").insert(payload).execute()
    return {"saved": True, "mode": "supabase", "data": result.data}
