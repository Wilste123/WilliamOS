"""Persist and load chat messages for cross-device continuity."""

from app.services.storage_service import create_record, delete_records, list_records


def list_chat_messages(limit: int = 40) -> list[dict]:
    messages = list_records("chat_history")
    chronological = sorted(messages, key=lambda item: item.get("created_at", ""))
    return chronological[-limit:]


def append_chat_messages(messages: list[dict]) -> int:
    saved = 0
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if not role or not content:
            continue
        create_record(
            "chat_history",
            {
                "role": role,
                "content": content,
            },
        )
        saved += 1
    return saved


def clear_chat_messages() -> bool:
    delete_records("chat_history")
    return True
