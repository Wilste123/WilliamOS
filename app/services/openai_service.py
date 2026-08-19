import json
import logging
import os
from collections.abc import Callable, Iterator
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

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
    if client is None:
        latest_message = next(
            (message["content"] for message in reversed(messages) if message["role"] == "user"),
            "",
        )
        return (
            "OpenAI er ikke konfigurert ennå. "
            "WilliamOS kjører fortsatt lokalt.\n\n"
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
    if client is None:
        return _NO_CLIENT_MSG

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


def chat_completion_stream(messages: list[dict], temperature: float = 0.3) -> Iterator[str]:
    """Yield text deltas from a streaming chat completion (no tools)."""
    if client is None:
        yield _NO_CLIENT_MSG
        return
    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        logger.error("OpenAI API stream failed: %s: %s", type(e).__name__, e)
        yield _API_ERROR_MSG


def chat_completion_with_tools_stream(
    messages: list[dict],
    tools: list[dict],
    tool_handler: Callable[[str, dict], Any],
    temperature: float = 0.3,
    max_iterations: int = 8,
) -> Iterator[tuple[str, str]]:
    """Stream assistant text; run tools between rounds without exposing tool JSON.

    Yields ``("status", phase)`` or ``("token", text)``.
    """
    if client is None:
        yield ("token", _NO_CLIENT_MSG)
        return

    current_messages = list(messages)
    yield ("status", "thinking")

    for _ in range(max_iterations):
        try:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=current_messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature,
                stream=True,
            )
        except Exception as e:
            logger.error("OpenAI API stream failed: %s: %s", type(e).__name__, e)
            yield ("token", _API_ERROR_MSG)
            return

        tool_acc: dict[int, dict[str, str]] = {}
        content_parts: list[str] = []
        finish_reason = None

        for chunk in stream:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            if choice.finish_reason:
                finish_reason = choice.finish_reason
            delta = choice.delta
            if delta is None:
                continue
            if delta.content:
                content_parts.append(delta.content)
                yield ("token", delta.content)
            if getattr(delta, "tool_calls", None):
                for tc in delta.tool_calls:
                    entry = tool_acc.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                    if tc.id:
                        entry["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            entry["name"] += tc.function.name
                        if tc.function.arguments:
                            entry["arguments"] += tc.function.arguments

        if finish_reason == "tool_calls" or tool_acc:
            for _, entry in sorted(tool_acc.items()):
                if entry.get("name"):
                    yield ("status", f"tool:{entry['name']}")
            current_messages.append(
                {
                    "role": "assistant",
                    "content": "".join(content_parts) or "",
                    "tool_calls": [
                        {
                            "id": entry["id"],
                            "type": "function",
                            "function": {"name": entry["name"], "arguments": entry["arguments"]},
                        }
                        for _, entry in sorted(tool_acc.items())
                    ],
                }
            )
            for _, entry in sorted(tool_acc.items()):
                try:
                    args = json.loads(entry["arguments"] or "{}")
                except json.JSONDecodeError:
                    args = {}
                try:
                    result = tool_handler(entry["name"], args)
                except Exception as exc:
                    logger.error("Tool %s failed: %s", entry["name"], exc)
                    result = {"error": str(exc)}
                current_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": entry["id"],
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )
            continue

        return

    yield ("token", "Maksimalt antall iterasjoner nådd uten endelig svar.")
