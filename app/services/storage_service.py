import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / ".williamos"
DATA_FILE = DATA_DIR / "local_store.json"
COLLECTIONS = [
    "assets",
    "tasks",
    "projects",
    "documents",
    "decisions",
    "events",
    "inbox_items",
]


def _default_state() -> dict:
    return {collection: [] for collection in COLLECTIONS}


def _ensure_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(_default_state(), indent=2), encoding="utf-8")


def load_state() -> dict:
    _ensure_storage()
    try:
        state = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        state = _default_state()
    for collection in COLLECTIONS:
        state.setdefault(collection, [])
    return state


def save_state(state: dict) -> None:
    _ensure_storage()
    DATA_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def list_records(collection: str) -> list[dict]:
    state = load_state()
    records = state.get(collection, [])
    return sorted(records, key=lambda item: item.get("created_at", ""), reverse=True)


def get_record(collection: str, record_id: str) -> dict | None:
    for record in load_state().get(collection, []):
        if record.get("id") == record_id:
            return record
    return None


def create_record(collection: str, payload: dict) -> dict:
    state = load_state()
    record = {
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    state[collection].append(record)
    save_state(state)
    return record


def update_record(collection: str, record_id: str, updates: dict) -> dict | None:
    state = load_state()
    for index, record in enumerate(state.get(collection, [])):
        if record.get("id") != record_id:
            continue
        state[collection][index] = {
            **record,
            **updates,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        save_state(state)
        return state[collection][index]
    return None


def append_event(
    title: str,
    event_type: str,
    notes: str | None = None,
    *,
    asset_id: str | None = None,
    project_id: str | None = None,
    decision_id: str | None = None,
    event_date: str | None = None,
) -> dict:
    return create_record(
        "events",
        {
            "title": title,
            "event_type": event_type,
            "notes": notes,
            "asset_id": asset_id,
            "project_id": project_id,
            "decision_id": decision_id,
            "event_date": event_date,
        },
    )
