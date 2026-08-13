from pathlib import Path
from app.services.openai_service import chat_completion
from app.services.memory_service import get_recent_memory_text
from app.agents.self_evolve import log_request_locally
from app.services.memory_service import save_memory

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "pa_system_prompt.txt"
DEFAULT_PROMPT = "You are WilliamOS, William's practical personal assistant. Answer in Norwegian."


def load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return DEFAULT_PROMPT

def handle_actions(message: str):
    msg = message.lower()

    if msg.startswith("husk "):
        text = message[5:]
        save_memory(text)

        return {
            "handled": True,
            "response": f"✅ Lagret i minnet: {text}"
        }

    return {
        "handled": False
    }

def ask_agent(message: str) -> str:

    action_result = handle_actions(message)

    if action_result["handled"]:
        return action_result["response"]

    log_request_locally(message)

    memory = get_recent_memory_text()
    system_prompt = load_system_prompt()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Relevant saved memory:\n{memory}"},
        {"role": "user", "content": message},
    ]

    return chat_completion(messages)

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
           
        }
    }
]

LOCAL_TASKS = []

def create_task(title: str):
    LOCAL_TASKS.append({
        "title": title,
        "done": False
    })
