import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

msvcrt = None

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None
    import msvcrt


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
WINDOWS_LOCK_SIZE = 2**31 - 1


def _default_state() -> dict:
    return {collection: [] for collection in COLLECTIONS}


def _ensure_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(_default_state(), indent=2), encoding="utf-8")


def _normalize_state(state: dict | None) -> dict:
    state = state or {}
    for collection in COLLECTIONS:
        state.setdefault(collection, [])
    return state


def _lock_file(handle, *, exclusive: bool) -> None:
    if fcntl is not None:
        mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(handle.fileno(), mode)
        return
    mode = msvcrt.LK_LOCK if exclusive else msvcrt.LK_RLCK
    handle.seek(0)
    msvcrt.locking(handle.fileno(), mode, WINDOWS_LOCK_SIZE)


def _unlock_file(handle) -> None:
    if fcntl is not None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return
    handle.seek(0)
    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, WINDOWS_LOCK_SIZE)


def _read_state(handle) -> dict:
    handle.seek(0)
    try:
        state = json.loads(handle.read() or "{}")
    except json.JSONDecodeError:
        state = _default_state()
    return _normalize_state(state)


def load_state() -> dict:
    _ensure_storage()
    with DATA_FILE.open("r", encoding="utf-8") as handle:
        _lock_file(handle, exclusive=False)
        try:
            return _read_state(handle)
        finally:
            _unlock_file(handle)


def save_state(state: dict) -> None:
    _ensure_storage()
    with DATA_FILE.open("r+", encoding="utf-8") as handle:
        _lock_file(handle, exclusive=True)
        try:
            handle.seek(0)
            json.dump(_normalize_state(state), handle, indent=2, ensure_ascii=False)
            handle.truncate()
        finally:
            _unlock_file(handle)


def mutate_state(mutator: Callable[[dict], Any]) -> Any:
    _ensure_storage()
    with DATA_FILE.open("r+", encoding="utf-8") as handle:
        _lock_file(handle, exclusive=True)
        try:
            state = _read_state(handle)
            result = mutator(state)
            handle.seek(0)
            json.dump(_normalize_state(state), handle, indent=2, ensure_ascii=False)
            handle.truncate()
            return result
        finally:
            _unlock_file(handle)


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
    def _mutate(state: dict) -> dict:
        record = {
            "id": str(uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        state[collection].append(record)
        return record

    return mutate_state(_mutate)


def update_record(collection: str, record_id: str, updates: dict) -> dict | None:
    def _mutate(state: dict) -> dict | None:
        for index, record in enumerate(state.get(collection, [])):
            if record.get("id") != record_id:
                continue
            state[collection][index] = {
                **record,
                **updates,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            return state[collection][index]
        return None

    return mutate_state(_mutate)


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
