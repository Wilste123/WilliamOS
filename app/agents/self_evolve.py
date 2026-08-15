from app.services.storage_service import create_record, list_records

SIGNAL_KEYWORDS = [
    "lån",
    "bolig",
    "bil",
    "hytte",
    "forsikring",
    "oppgave",
    "prosjekt",
    "dokument",
    "service",
]


def log_request(request_text: str) -> None:
    """Log a chat request to Supabase for self-evolve analysis."""
    create_record(
        "requests_log",
        {"request_text": request_text.strip()},
    )


def analyze_requests() -> dict:
    """Analyze logged requests and surface recurring keyword signals."""
    rows = list_records("requests_log")
    keywords: dict[str, int] = {}
    for row in rows:
        text = row.get("request_text", "").lower()
        for word in SIGNAL_KEYWORDS:
            if word in text:
                keywords[word] = keywords.get(word, 0) + 1
    top = sorted(keywords.items(), key=lambda item: item[1], reverse=True)
    return {"count": len(rows), "top_signals": top}
