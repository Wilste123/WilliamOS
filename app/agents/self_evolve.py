from pathlib import Path
from datetime import datetime

LOG_PATH = Path("requests_log_local.txt")


def log_request_locally(request_text: str) -> None:
    """Temporary local logger before Supabase is connected."""
    line = f"{datetime.utcnow().isoformat()} | {request_text.strip()}\n"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)


def analyze_requests_locally() -> dict:
    if not LOG_PATH.exists():
        return {"count": 0, "top_signals": []}
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    keywords = {}
    for line in lines:
        text = line.lower()
        for word in ["lån", "bolig", "bil", "hytte", "forsikring", "oppgave", "prosjekt", "dokument", "service"]:
            if word in text:
                keywords[word] = keywords.get(word, 0) + 1
    top = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
    return {"count": len(lines), "top_signals": top}
