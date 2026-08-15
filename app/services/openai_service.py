import json
import logging
import os
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.services.user_context import get_current_assistant_name

load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

_NO_CLIENT_MSG = (
    "OpenAI er ikke konfigurert ennå. "
    "WilliamOS kjører fortsatt lokalt.\n\n"
    "Bruk kommandoer som 'lag oppgave ...', 'lag eiendel ...', "
    "'lag prosjekt ...' eller 'lag beslutning ...' for å opprette data."
)

_API_ERROR_MSG = (
    "OpenAI-kallet feilet. Sjekk dette:\n"
    "1. At OPENAI_API_KEY ligger i .env\n"
    "2. At API-nøkkelen er gyldig\n"
    "3. At OPENAI_MODEL finnes for kontoen din\n"
    "4. At OpenAI-kontoen har billing/credits\n"
)


def chat_completion(messages: list[dict], temperature: float = 0.3) -> str:
    assistant_name = get_current_assistant_name()
    if client is None:
        latest_message = next(
            (message["content"] for message in reversed(messages) if message["role"] == "user"),
            "",
        )
        return (
            "OpenAI er ikke konfigurert ennå. "
            f"{assistant_name} kjører fortsatt lokalt.\n\n"
            f"Siste melding: {latest_message}\n"
            "Hvis dette skal utføres i systemet, bruk kommandoer som "
            "'lag oppgave ...', 'lag eiendel ...', 'lag prosjekt ...' eller 'lag beslutning ...'."
        )
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
        )

        return response.choices[0].message.content or ""

    except Exception as e:
        logger.error("OpenAI API call failed: %s: %s", type(e).__name__, e)
        return _API_ERROR_MSG


def chat_completion_with_tools(
    messages: list[dict],
    tools: list[dict],
    tool_handler: Callable[[str, dict], Any],
    temperature: float = 0.3,
    max_iterations: int = 8,
) -> str:
    """Run a chat completion loop that can call tools.

    ``tool_handler(function_name, arguments_dict)`` is called for each tool
    invocation and must return a JSON-serialisable value.  The loop continues
    until the model stops requesting tool calls or ``max_iterations`` is
    exhausted.
    """
    assistant_name = get_current_assistant_name()
    if client is None:
        return _NO_CLIENT_MSG.replace("WilliamOS", assistant_name)

    current_messages = list(messages)

    for _ in range(max_iterations):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=current_messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature,
            )
        except Exception as e:
            logger.error("OpenAI API call failed: %s: %s", type(e).__name__, e)
            return _API_ERROR_MSG

        choice = response.choices[0]
        msg = choice.message

        if choice.finish_reason == "tool_calls" and msg.tool_calls:
            # Append the assistant message with tool_calls intact
            assistant_entry: dict = {"role": "assistant", "content": msg.content or ""}
            assistant_entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
            current_messages.append(assistant_entry)

            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                try:
                    result = tool_handler(tc.function.name, args)
                except Exception as exc:
                    logger.error("Tool %s failed: %s", tc.function.name, exc)
                    result = {"error": str(exc)}
                current_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )
        else:
            return msg.content or ""

    return "Maksimalt antall iterasjoner nådd uten endelig svar."
