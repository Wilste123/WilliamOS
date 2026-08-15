from pathlib import Path
from datetime import datetime, timezone

from app.services.storage_service import create_record, list_records

LOG_PATH = Path("requests_log_local.txt")


def log_request_locally(request_text: str) -> None:
    """Log request to per-user storage when available, otherwise use local fallback."""
    try:
        create_record("requests_log", {"request_text": request_text.strip()})
        return
    except Exception:
        line = f"{datetime.now(timezone.utc).isoformat()} | {request_text.strip()}\n"
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line)


def analyze_requests_locally() -> dict:
    try:
        rows = list_records("requests_log")
        keywords = {}
        for row in rows:
            text = (row.get("request_text") or "").lower()
            for word in ["lån", "bolig", "bil", "hytte", "forsikring", "oppgave", "prosjekt", "dokument", "service"]:
                if word in text:
                    keywords[word] = keywords.get(word, 0) + 1
        top = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        return {"count": len(rows), "top_signals": top}
    except Exception:
        pass
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
