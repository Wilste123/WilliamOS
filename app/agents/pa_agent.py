from pathlib import Path
import re

from app.services.openai_service import chat_completion
from app.services.memory_service import get_recent_memory_text
from app.agents.self_evolve import log_request_locally
from app.services.memory_service import save_memory
from app.services.retrieval_service import build_document_context
from app.services.action_engine import (
    build_dashboard_summary,
    capture_inbox_entry,
    create_asset,
    create_decision,
    create_project,
    create_task,
)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "pa_system_prompt.txt"
DEFAULT_PROMPT = "You are WilliamOS, William's practical personal assistant. Answer in Norwegian."


def load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return DEFAULT_PROMPT

def handle_actions(message: str):
    msg = message.strip()
    lowered = msg.lower()

    if lowered.startswith("husk "):
        text = message[5:]
        save_memory(text)

        return {
            "handled": True,
            "response": f"✅ Lagret i minnet: {text}"
        }

    action_patterns = [
        ("task", r"^(lag|opprett)\s+oppgave\s+(?P<content>.+)$"),
        ("asset", r"^(lag|opprett)\s+(eiendel|asset)\s+(?P<content>.+)$"),
        ("project", r"^(lag|opprett)\s+prosjekt\s+(?P<content>.+)$"),
        ("decision", r"^(lag|opprett)\s+beslutning\s+(?P<content>.+)$"),
        ("inbox", r"^(fang|legg)\s+i\s+innboks\s+(?P<content>.+)$"),
    ]

    for action_type, pattern in action_patterns:
        match = re.match(pattern, msg, flags=re.IGNORECASE)
        if not match:
            continue
        content = match.group("content").strip()
        if action_type == "task":
            task = create_task({"title": content, "priority": 2, "status": "open"})
            return {"handled": True, "response": f"✅ Oppgave opprettet: {task['title']}"}
        if action_type == "asset":
            asset = create_asset({"name": content, "status": "active"})
            return {"handled": True, "response": f"✅ Eiendel opprettet: {asset['name']}"}
        if action_type == "project":
            project = create_project({"name": content, "status": "active"})
            return {"handled": True, "response": f"✅ Prosjekt opprettet: {project['name']}"}
        if action_type == "decision":
            decision = create_decision({"title": content, "status": "open"})
            return {"handled": True, "response": f"✅ Beslutning opprettet: {decision['title']}"}
        if action_type == "inbox":
            inbox_item = capture_inbox_entry(content)
            return {
                "handled": True,
                "response": (
                    f"✅ Lagret i inbox. "
                    f"Forslag generert: {len(inbox_item.get('suggestions', []))}"
                ),
            }

    if lowered == "vis dashboard":
        dashboard = build_dashboard_summary()
        metrics = dashboard["metrics"]
        return {
            "handled": True,
            "response": (
                "📊 Dashboard\n"
                f"- Åpne oppgaver: {metrics['open_tasks']}\n"
                f"- Aktive prosjekter: {metrics['projects']}\n"
                f"- Eiendeler: {metrics['assets']}\n"
                f"- Åpne beslutninger: {metrics['open_decisions']}"
            ),
        }

    return {
        "handled": False
    }

def ask_agent(message: str, *, use_documents: bool = True) -> tuple[str, list[dict]]:
    """
    Returns (answer, sources) where sources is a list of document result dicts.
    sources is empty when no documents were used or use_documents is False.
    """
    action_result = handle_actions(message)

    if action_result["handled"]:
        return action_result["response"], []

    log_request_locally(message)

    memory = get_recent_memory_text()
    system_prompt = load_system_prompt()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Relevant saved memory:\n{memory}"},
    ]

    sources: list[dict] = []
    if use_documents:
        doc_context, sources = build_document_context(message)
        if doc_context:
            messages.append({"role": "system", "content": doc_context})

    messages.append({"role": "user", "content": message})

    answer = chat_completion(messages)
    return answer, sources
