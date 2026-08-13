from pathlib import Path
import re

from app.services.openai_service import chat_completion, chat_completion_with_tools
from app.services.memory_service import get_recent_memory_text
from app.agents.self_evolve import log_request_locally
from app.services.memory_service import save_memory
from app.services.retrieval_service import build_document_context
from app.services.storage_service import list_records
from app.services.action_engine import (
    build_dashboard_summary,
    capture_inbox_entry,
    create_asset,
    create_decision,
    create_project,
    create_task,
    update_asset,
    update_task,
)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "pa_system_prompt.txt"
DEFAULT_PROMPT = "You are WilliamOS, William's practical personal assistant. Answer in Norwegian."

# ---------------------------------------------------------------------------
# Tool schemas – exposed to the OpenAI model via function calling
# ---------------------------------------------------------------------------

WILLIAMOS_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "create_asset",
            "description": "Opprett en ny eiendel (bil, båt, bolig, utstyr, etc.) i WilliamOS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Navn på eiendelen"},
                    "type": {"type": "string", "description": "Type eiendel, f.eks. bil, båt, bolig"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "considering_purchase", "inactive"],
                        "description": "Status for eiendelen",
                    },
                    "description": {"type": "string", "description": "Beskrivelse eller notater"},
                    "estimated_value": {"type": "number", "description": "Estimert verdi i NOK"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_asset",
            "description": "Oppdater en eksisterende eiendel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string", "description": "ID til eiendelen som skal oppdateres"},
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["active", "considering_purchase", "inactive"],
                    },
                    "description": {"type": "string"},
                    "estimated_value": {"type": "number"},
                },
                "required": ["asset_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_assets",
            "description": "Hent liste over alle eiendeler i WilliamOS.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Opprett en ny oppgave, eventuelt knyttet til en eiendel eller et prosjekt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Tittel på oppgaven"},
                    "description": {"type": "string", "description": "Utfyllende beskrivelse"},
                    "due_date": {"type": "string", "description": "Frist i format YYYY-MM-DD"},
                    "priority": {
                        "type": "integer",
                        "enum": [1, 2, 3],
                        "description": "Prioritet: 1=lav, 2=middels, 3=høy",
                    },
                    "asset_id": {"type": "string", "description": "ID til tilknyttet eiendel"},
                    "project_id": {"type": "string", "description": "ID til tilknyttet prosjekt"},
                    "status": {
                        "type": "string",
                        "enum": ["open", "in_progress", "completed"],
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Oppdater en eksisterende oppgave.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "ID til oppgaven som skal oppdateres"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["open", "in_progress", "completed"]},
                    "completed": {"type": "boolean"},
                    "due_date": {"type": "string"},
                    "priority": {"type": "integer"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Hent liste over alle oppgaver.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_project",
            "description": "Opprett et nytt prosjekt, eventuelt knyttet til en eiendel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Navn på prosjektet"},
                    "status": {"type": "string", "enum": ["active", "on_hold", "done"]},
                    "next_action": {"type": "string", "description": "Neste konkrete handling"},
                    "notes": {"type": "string", "description": "Notater"},
                    "asset_id": {"type": "string", "description": "ID til tilknyttet eiendel"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_projects",
            "description": "Hent liste over alle prosjekter.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_decision",
            "description": "Registrer en beslutning, eventuelt knyttet til en eiendel eller et prosjekt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Tittel på beslutningen"},
                    "summary": {"type": "string", "description": "Sammendrag / beskrivelse"},
                    "status": {"type": "string", "enum": ["open", "decided", "paused"]},
                    "asset_id": {"type": "string", "description": "ID til tilknyttet eiendel"},
                    "project_id": {"type": "string", "description": "ID til tilknyttet prosjekt"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_decisions",
            "description": "Hent liste over alle beslutninger.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_documents",
            "description": "Hent liste over dokumenter, valgfritt filtrert på eiendel eller prosjekt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string", "description": "Filtrer på eiendel-ID"},
                    "project_id": {"type": "string", "description": "Filtrer på prosjekt-ID"},
                },
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool executor – maps function names to real Python calls
# ---------------------------------------------------------------------------

def _execute_tool(func_name: str, args: dict) -> object:
    clean = {k: v for k, v in args.items() if v is not None}

    if func_name == "create_asset":
        return create_asset(clean)
    if func_name == "update_asset":
        asset_id = clean.pop("asset_id")
        return update_asset(asset_id, clean) or {"error": "Eiendel ikke funnet"}
    if func_name == "list_assets":
        return list_records("assets")

    if func_name == "create_task":
        payload = {"priority": 2, "status": "open", **clean}
        return create_task(payload)
    if func_name == "update_task":
        task_id = clean.pop("task_id")
        return update_task(task_id, clean) or {"error": "Oppgave ikke funnet"}
    if func_name == "list_tasks":
        return list_records("tasks")

    if func_name == "create_project":
        payload = {"status": "active", **clean}
        return create_project(payload)
    if func_name == "list_projects":
        return list_records("projects")

    if func_name == "create_decision":
        payload = {"status": "open", **clean}
        return create_decision(payload)
    if func_name == "list_decisions":
        return list_records("decisions")

    if func_name == "list_documents":
        docs = list_records("documents")
        if clean.get("asset_id"):
            docs = [d for d in docs if d.get("asset_id") == clean["asset_id"]]
        if clean.get("project_id"):
            docs = [d for d in docs if d.get("project_id") == clean["project_id"]]
        return docs

    return {"error": f"Ukjent funksjon: {func_name}"}


# ---------------------------------------------------------------------------
# System prompt loading
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return DEFAULT_PROMPT


# ---------------------------------------------------------------------------
# Simple regex-based action handler (fast path, no LLM needed)
# ---------------------------------------------------------------------------

def handle_actions(message: str):
    msg = message.strip()
    lowered = msg.lower()

    if lowered.startswith("husk "):
        text = message[5:]
        save_memory(text)
        return {"handled": True, "response": f"✅ Lagret i minnet: {text}"}

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

    return {"handled": False}


# ---------------------------------------------------------------------------
# Main agent entry point
# ---------------------------------------------------------------------------

def ask_agent(
    message: str,
    *,
    use_documents: bool = True,
    history: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    """Return (answer, sources).

    ``history`` is an optional list of previous ``{"role": ..., "content": ...}``
    messages (user + assistant only) from the current conversation session.
    Including history lets the model remember context across turns so it can
    execute actions like "lagre eiendelen" after the user has already described
    the asset in a previous message.
    """
    action_result = handle_actions(message)
    if action_result["handled"]:
        return action_result["response"], []

    log_request_locally(message)

    memory = get_recent_memory_text()
    system_prompt = load_system_prompt()

    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Relevant saved memory:\n{memory}"},
    ]

    sources: list[dict] = []
    if use_documents:
        doc_context, sources = build_document_context(message)
        if doc_context:
            messages.append({"role": "system", "content": doc_context})

    # Inject prior conversation turns so the model has full context
    if history:
        for entry in history:
            if entry.get("role") in ("user", "assistant"):
                messages.append({"role": entry["role"], "content": entry.get("content") or ""})

    messages.append({"role": "user", "content": message})

    answer = chat_completion_with_tools(messages, WILLIAMOS_TOOLS, _execute_tool)
    return answer, sources
