import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY mangler i .env-filen. "
        "Lag en .env-fil i prosjektroten og legg inn OPENAI_API_KEY=din_nokkel"
    )

client = OpenAI(api_key=OPENAI_API_KEY)


def chat_completion(messages: list[dict], temperature: float = 0.3) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
        )

        return response.choices[0].message.content or ""

    except Exception as e:
        return (
            "OpenAI-kallet feilet.\n\n"
            f"Modell brukt: {MODEL}\n"
            f"Feiltype: {type(e).__name__}\n"
            f"Feilmelding: {str(e)}\n\n"
            "Sjekk dette:\n"
            "1. At OPENAI_API_KEY ligger i .env\n"
            "2. At API-nøkkelen er gyldig\n"
            "3. At OPENAI_MODEL finnes for kontoen din\n"
            "4. At OpenAI-kontoen har billing/credits\n"
        )
