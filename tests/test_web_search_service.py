import json
from unittest.mock import MagicMock, patch

from app.services.web_search_service import search_web


def test_search_web_empty_query():
    assert search_web("  ") == []


def test_search_web_missing_api_key(monkeypatch):
    monkeypatch.setattr("app.services.web_search_service.SERPER_API_KEY", None)
    result = search_web("test query")
    assert len(result) == 1
    assert "error" in result[0]


def test_search_web_parses_organic_results(monkeypatch):
    monkeypatch.setattr("app.services.web_search_service.SERPER_API_KEY", "test-key")
    payload = {
        "organic": [
            {"title": "Result A", "link": "https://a.example", "snippet": "Snippet A"},
            {"title": "Result B", "link": "https://b.example", "snippet": "Snippet B"},
        ]
    }

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode()
    mock_response.__enter__ = lambda self: self
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        results = search_web("boat repair", num_results=2)

    assert len(results) == 2
    assert results[0]["title"] == "Result A"
    assert results[0]["url"] == "https://a.example"
    assert results[1]["snippet"] == "Snippet B"
