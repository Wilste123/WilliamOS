import logging
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


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
        return (
            "OpenAI-kallet feilet. Sjekk dette:\n"
            "1. At OPENAI_API_KEY ligger i .env\n"
            "2. At API-nøkkelen er gyldig\n"
            "3. At OPENAI_MODEL finnes for kontoen din\n"
            "4. At OpenAI-kontoen har billing/credits\n"
        )
