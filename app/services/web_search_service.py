"""Serper-powered web search for the PA agent."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_SEARCH_URL = "https://google.serper.dev/search"


def search_web(query: str, *, num_results: int = 5) -> list[dict]:
    """Search the web via Serper. Returns [{title, url, snippet}]."""
    cleaned = query.strip()
    if not cleaned:
        return []

    if not SERPER_API_KEY:
        return [{"error": "SERPER_API_KEY er ikke satt i .env"}]

    payload = json.dumps({"q": cleaned, "num": max(1, min(num_results, 10))}).encode()
    request = urllib.request.Request(
        SERPER_SEARCH_URL,
        data=payload,
        method="POST",
        headers={
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        logger.error("Serper HTTP error %s: %s", exc.code, body[:200])
        return [{"error": f"Web-søk feilet (HTTP {exc.code})"}]
    except urllib.error.URLError as exc:
        logger.error("Serper network error: %s", exc)
        return [{"error": "Kunne ikke nå Serper API"}]
    except json.JSONDecodeError:
        return [{"error": "Ugyldig svar fra Serper"}]

    results: list[dict] = []
    for item in data.get("organic", [])[:num_results]:
        results.append(
            {
                "title": item.get("title") or "",
                "url": item.get("link") or "",
                "snippet": item.get("snippet") or "",
            }
        )
    return results
