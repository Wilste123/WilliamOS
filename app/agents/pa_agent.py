from pathlib import Path
import re

from app.services.openai_service import chat_completion_with_tools, chat_completion_with_tools_stream
from app.services.profile_service import DEFAULT_ASSISTANT_NAME, get_assistant_name
from app.agents.self_evolve import log_request
from app.services.memory_service import get_recent_memory_text, save_memory
from app.services.retrieval_service import build_document_context
from app.services.storage_service import list_records
from app.services.action_engine import (
    build_dashboard_summary,
    build_priority_engine,
    build_weekly_brief,
    capture_inbox_entry,
    create_asset,
    create_decision,
    create_document,
    create_project,
    create_task,
    update_asset,
    update_decision,
    update_project,
    update_task,
)
from app.services.chat_actions import merge_chat_actions, tool_result_to_action

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
            "name": "update_project",
            "description": "Oppdater et eksisterende prosjekt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "ID til prosjektet som skal oppdateres"},
                    "name": {"type": "string"},
                    "status": {"type": "string", "enum": ["active", "on_hold", "done"]},
                    "next_action": {"type": "string"},
                    "notes": {"type": "string"},
                    "asset_id": {"type": "string"},
                },
                "required": ["project_id"],
            },
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
            "name": "update_decision",
            "description": "Oppdater en eksisterende beslutning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "decision_id": {"type": "string", "description": "ID til beslutningen som skal oppdateres"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "status": {"type": "string", "enum": ["open", "decided", "paused"]},
                    "asset_id": {"type": "string"},
                    "project_id": {"type": "string"},
                },
                "required": ["decision_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_document",
            "description": "Registrer et dokument i databasen (f.eks. etter opplasting).",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Filnavn"},
                    "storage_path": {"type": "string", "description": "Lagringsbane"},
                    "text_content": {"type": "string", "description": "Tekstinnhold"},
                    "source_module": {"type": "string", "description": "Modul dokumentet tilhører"},
                    "asset_id": {"type": "string"},
                    "project_id": {"type": "string"},
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_priority_focus",
            "description": "Hent rangert topp-5 fokusliste fra oppgaver, mål, prosjekter og inbox. Bruk når brukeren spør hva de bør prioritere.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weekly_brief",
            "description": "Hent ukens brief med prioriterte oppgaver, aktive prosjekter, åpne beslutninger og kommende hendelser. Bruk når brukeren spør hva de bør gjøre denne uka.",
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

def _execute_tool(func_name: str, args: dict, *, action_log: list[dict] | None = None) -> object:
    clean = {k: v for k, v in args.items() if v is not None}

    try:
        if func_name == "create_asset":
            result = create_asset(clean)
        elif func_name == "update_asset":
            asset_id = clean.pop("asset_id")
            result = update_asset(asset_id, clean) or {"error": "Eiendel ikke funnet"}
        elif func_name == "list_assets":
            result = list_records("assets")
        elif func_name == "create_task":
            payload = {"priority": 2, "status": "open", **clean}
            result = create_task(payload)
        elif func_name == "update_task":
            task_id = clean.pop("task_id")
            result = update_task(task_id, clean) or {"error": "Oppgave ikke funnet"}
        elif func_name == "list_tasks":
            result = list_records("tasks")
        elif func_name == "create_project":
            payload = {"status": "active", **clean}
            result = create_project(payload)
        elif func_name == "update_project":
            project_id = clean.pop("project_id")
            result = update_project(project_id, clean) or {"error": "Prosjekt ikke funnet"}
        elif func_name == "list_projects":
            result = list_records("projects")
        elif func_name == "create_decision":
            payload = {"status": "open", **clean}
            result = create_decision(payload)
        elif func_name == "update_decision":
            decision_id = clean.pop("decision_id")
            result = update_decision(decision_id, clean) or {"error": "Beslutning ikke funnet"}
        elif func_name == "list_decisions":
            result = list_records("decisions")
        elif func_name == "create_document":
            payload = {"source_module": "chat", **clean}
            result = create_document(payload)
        elif func_name == "get_weekly_brief":
            result = build_weekly_brief()
        elif func_name == "get_priority_focus":
            result = build_priority_engine()
        elif func_name == "list_documents":
            docs = list_records("documents")
            if clean.get("asset_id"):
                docs = [d for d in docs if d.get("asset_id") == clean["asset_id"]]
            if clean.get("project_id"):
                docs = [d for d in docs if d.get("project_id") == clean["project_id"]]
            result = docs
        else:
            result = {"error": f"Ukjent funksjon: {func_name}"}

    except Exception as exc:  # noqa: BLE001
        result = {"error": f"Lagring feilet for {func_name}: {exc}"}

    if action_log is not None:
        action = tool_result_to_action(func_name, args, result)
        if action:
            action_log.append(action)
    return result


# ---------------------------------------------------------------------------
# System prompt loading
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return DEFAULT_PROMPT


def build_system_prompt(
    assistant_name: str | None = None,
    user_name: str | None = None,
) -> str:
    """Personalize the base prompt with assistant and user names."""
    name = (assistant_name or DEFAULT_ASSISTANT_NAME).strip() or DEFAULT_ASSISTANT_NAME
    user_label = (user_name or "brukeren").strip() or "brukeren"
    base = load_system_prompt()

    lines = [
        line
        for line in base.splitlines()
        if not line.startswith("You are WilliamOS,")
    ]
    body = "\n".join(lines).strip()
    body = body.replace("WilliamOS workspace", f"{name} workspace")
    body = body.replace("help William stay on top of:", f"help {user_label} stay on top of:")

    return (
        f"You are {name}, {user_label}'s personal AI assistant.\n"
        f"When speaking to the user, refer to yourself as {name}.\n\n"
        f"{body}"
    )


# ---------------------------------------------------------------------------
# Simple regex-based action handler (fast path, no LLM needed)
# ---------------------------------------------------------------------------

def handle_actions(message: str):
    msg = message.strip()
    lowered = msg.lower()
    actions: list[dict] = []

    if lowered.startswith("husk "):
        text = message[5:]
        save_memory(text)
        return {"handled": True, "response": f"✅ Lagret i minnet: {text}", "actions": actions}

    action_patterns = [
        ("task", "create_task", r"^(lag|opprett)\s+oppgave\s+(?P<content>.+)$"),
        ("asset", "create_asset", r"^(lag|opprett)\s+(eiendel|asset)\s+(?P<content>.+)$"),
        ("project", "create_project", r"^(lag|opprett)\s+prosjekt\s+(?P<content>.+)$"),
        ("decision", "create_decision", r"^(lag|opprett)\s+beslutning\s+(?P<content>.+)$"),
        ("inbox", "capture_inbox", r"^(fang|legg)\s+i\s+innboks\s+(?P<content>.+)$"),
    ]

    for action_type, func_name, pattern in action_patterns:
        match = re.match(pattern, msg, flags=re.IGNORECASE)
        if not match:
            continue
        content = match.group("content").strip()
        if action_type == "task":
            task = create_task({"title": content, "priority": 2, "status": "open"})
            action = tool_result_to_action(func_name, {"title": content}, task)
            if action:
                actions.append(action)
            return {"handled": True, "response": f"✅ Oppgave opprettet: {task['title']}", "actions": actions}
        if action_type == "asset":
            asset = create_asset({"name": content, "status": "active"})
            action = tool_result_to_action(func_name, {"name": content}, asset)
            if action:
                actions.append(action)
            return {"handled": True, "response": f"✅ Eiendel opprettet: {asset['name']}", "actions": actions}
        if action_type == "project":
            project = create_project({"name": content, "status": "active"})
            action = tool_result_to_action(func_name, {"name": content}, project)
            if action:
                actions.append(action)
            return {"handled": True, "response": f"✅ Prosjekt opprettet: {project['name']}", "actions": actions}
        if action_type == "decision":
            decision = create_decision({"title": content, "status": "open"})
            action = tool_result_to_action(func_name, {"title": content}, decision)
            if action:
                actions.append(action)
            return {"handled": True, "response": f"✅ Beslutning opprettet: {decision['title']}", "actions": actions}
        if action_type == "inbox":
            inbox_item = capture_inbox_entry(content)
            return {
                "handled": True,
                "response": (
                    f"✅ Lagret i inbox. "
                    f"Forslag generert: {len(inbox_item.get('suggestions', []))}"
                ),
                "actions": actions,
            }

    weekly_triggers = (
        "hva bør jeg gjøre denne uka",
        "hva bør jeg gjøre denne uken",
        "ukens prioriteringer",
        "ukens brief",
        "hva bør jeg prioritere",
        "hva bør jeg fokusere på",
    )
    if any(trigger in lowered for trigger in weekly_triggers):
        brief = build_weekly_brief()
        return {"handled": True, "response": brief["summary_text"], "actions": actions}

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
            "actions": actions,
        }

    return {"handled": False, "actions": actions}


# ---------------------------------------------------------------------------
# Main agent entry point
# ---------------------------------------------------------------------------

def _normalize_history(raw: list[dict]) -> list[dict]:
    """Return a clean list of ``{"role", "content"}`` dicts from *raw*.

    The UI may store extra keys (e.g. ``sources``) alongside role/content.
    Only ``user`` and ``assistant`` entries are kept; system entries and any
    unknown keys are dropped so the LLM context stays well-formed.
    """
    return [
        {"role": entry["role"], "content": entry.get("content") or ""}
        for entry in raw
        if entry.get("role") in ("user", "assistant")
    ]


def _build_agent_messages(
    message: str,
    *,
    use_documents: bool = True,
    history: list[dict] | None = None,
    document_id: str | None = None,
) -> tuple[list[dict], list[dict]]:
    from app.services.auth_context import get_current_context

    context = get_current_context()
    assistant_name = get_assistant_name()
    memory = get_recent_memory_text()
    system_prompt = build_system_prompt(
        assistant_name=assistant_name,
        user_name=context.display_name if context else None,
    )

    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Relevant saved memory:\n{memory}"},
    ]

    sources: list[dict] = []
    if use_documents:
        doc_context, sources = build_document_context(message, document_id=document_id)
        if doc_context:
            messages.append({"role": "system", "content": doc_context})

    if history:
        messages.extend(_normalize_history(history))

    messages.append({"role": "user", "content": message})
    return messages, sources


def ask_agent(
    message: str,
    *,
    use_documents: bool = True,
    history: list[dict] | None = None,
    document_id: str | None = None,
) -> tuple[str, list[dict]]:
    """Return (answer, sources).

    ``history`` is an optional list of previous conversation messages from
    the current session.  Entries may contain extra UI-layer keys (e.g.
    ``sources``); this function normalises them internally so the caller
    does not need to pre-filter.  Only ``user`` and ``assistant`` roles are
    forwarded to the model.
    """
    action_result = handle_actions(message)
    if action_result["handled"]:
        return action_result["response"], []

    log_request(message)
    messages, sources = _build_agent_messages(
        message, use_documents=use_documents, history=history, document_id=document_id
    )
    answer = chat_completion_with_tools(messages, WILLIAMOS_TOOLS, _execute_tool)
    return answer, sources


def ask_agent_stream(
    message: str,
    *,
    use_documents: bool = True,
    history: list[dict] | None = None,
    document_id: str | None = None,
):
    """Yield SSE-ready dicts: status, token, done, or error."""
    action_result = handle_actions(message)
    if action_result["handled"]:
        yield {"type": "token", "text": action_result["response"]}
        yield {
            "type": "done",
            "sources": [],
            "actions": action_result.get("actions") or [],
        }
        return

    log_request(message)
    messages, sources = _build_agent_messages(
        message, use_documents=use_documents, history=history, document_id=document_id
    )
    completed_actions: list[dict] = []
    assistant_text = ""

    def tool_handler(func_name: str, args: dict):
        return _execute_tool(func_name, args, action_log=completed_actions)

    try:
        for kind, value in chat_completion_with_tools_stream(
            messages, WILLIAMOS_TOOLS, tool_handler
        ):
            if kind == "status":
                yield {"type": "status", "phase": value}
            else:
                assistant_text += value
                yield {"type": "token", "text": value}
        yield {
            "type": "done",
            "sources": sources,
            "actions": merge_chat_actions(completed_actions, assistant_text),
        }
    except Exception as exc:
        yield {"type": "error", "message": str(exc)}
