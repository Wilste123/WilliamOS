"""Tests for cross-module document intelligence pipeline."""

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store_with_doc(text_content: str, filename: str = "report.txt", source_module: str = "documents"):
    """Return a minimal store dict containing one document record."""
    return {
        "documents": [
            {
                "id": "doc-001",
                "filename": filename,
                "storage_path": f"uploads/{filename}",
                "text_content": text_content,
                "source_module": source_module,
                "asset_id": None,
                "project_id": None,
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ]
    }


# ---------------------------------------------------------------------------
# 1. Text extraction
# ---------------------------------------------------------------------------

class TestExtractTextContent:
    from app.services.document_service import extract_text_content

    def test_plain_text_extracted(self):
        from app.services.document_service import extract_text_content
        result = extract_text_content("notes.txt", b"Hello world")
        assert result == "Hello world"

    def test_markdown_extracted(self):
        from app.services.document_service import extract_text_content
        result = extract_text_content("README.md", b"# Title\nSome content here.")
        assert "Title" in result

    def test_binary_returns_none(self):
        from app.services.document_service import extract_text_content
        binary = bytes(range(256))
        result = extract_text_content("image.png", binary)
        assert result is None

    def test_empty_content_returns_none(self):
        from app.services.document_service import extract_text_content
        result = extract_text_content("empty.txt", b"")
        assert result is None

    def test_large_file_truncated(self):
        from app.services.document_service import extract_text_content, MAX_TEXT_BYTES
        large = b"A" * (MAX_TEXT_BYTES + 10_000)
        result = extract_text_content("big.txt", large)
        assert result is not None
        assert len(result) <= MAX_TEXT_BYTES


# ---------------------------------------------------------------------------
# 2. Document storage includes new fields
# ---------------------------------------------------------------------------

class TestSaveUploadedFile:
    def test_returns_text_content_for_text_file(self, tmp_path, monkeypatch):
        from app.services import document_service
        monkeypatch.setattr(document_service, "UPLOAD_DIR", tmp_path)
        result = document_service.save_uploaded_file("hello.txt", b"Budget: 100 NOK")
        assert result["text_content"] == "Budget: 100 NOK"
        assert result["filename"] == "hello.txt"
        assert "storage_path" in result

    def test_returns_none_text_for_binary(self, tmp_path, monkeypatch):
        from app.services import document_service
        monkeypatch.setattr(document_service, "UPLOAD_DIR", tmp_path)
        result = document_service.save_uploaded_file("photo.jpg", bytes(range(256)))
        assert result["text_content"] is None


# ---------------------------------------------------------------------------
# 3. Retrieval service
# ---------------------------------------------------------------------------

class TestRetrievalService:

    def _patch_storage(self, monkeypatch, store):
        import app.services.retrieval_service as rs
        monkeypatch.setattr(rs, "list_records", lambda _: store.get("documents", []))

    def test_relevant_doc_returned(self, monkeypatch):
        from app.services import retrieval_service as rs
        store = _make_store_with_doc("The quarterly budget is 500 000 NOK", source_module="projects")
        self._patch_storage(monkeypatch, store)
        results = rs.search_documents("budget NOK")
        assert len(results) >= 1
        assert results[0]["filename"] == "report.txt"
        assert results[0]["score"] > 0

    def test_no_match_returns_empty(self, monkeypatch):
        from app.services import retrieval_service as rs
        store = _make_store_with_doc("Totally unrelated content about animals")
        self._patch_storage(monkeypatch, store)
        results = rs.search_documents("budget invoice payment")
        assert results == []

    def test_source_module_filter(self, monkeypatch):
        from app.services import retrieval_service as rs
        store = {
            "documents": [
                {"id": "1", "filename": "a.txt", "text_content": "budget report", "source_module": "projects", "asset_id": None, "project_id": None, "created_at": None},
                {"id": "2", "filename": "b.txt", "text_content": "budget invoice", "source_module": "documents", "asset_id": None, "project_id": None, "created_at": None},
            ]
        }
        self._patch_storage(monkeypatch, store)
        results = rs.search_documents("budget", source_module="projects")
        assert all(r["source_module"] == "projects" for r in results)

    def test_snippet_included(self, monkeypatch):
        from app.services import retrieval_service as rs
        store = _make_store_with_doc("Maintenance cost for the boat was 12 000 NOK in Q1.")
        self._patch_storage(monkeypatch, store)
        results = rs.search_documents("boat maintenance cost")
        assert results[0]["snippet"] != ""

    def test_build_document_context_returns_context_and_sources(self, monkeypatch):
        from app.services import retrieval_service as rs
        store = _make_store_with_doc("Monthly recurring invoice for cloud services.", source_module="assets")
        self._patch_storage(monkeypatch, store)
        context, sources = rs.build_document_context("invoice cloud")
        assert "invoice" in context.lower() or "cloud" in context.lower()
        assert len(sources) >= 1

    def test_empty_query_returns_nothing(self, monkeypatch):
        from app.services import retrieval_service as rs
        store = _make_store_with_doc("Some content")
        self._patch_storage(monkeypatch, store)
        results = rs.search_documents("   ")
        assert results == []


# ---------------------------------------------------------------------------
# 4. Chat agent — documents injected into context
# ---------------------------------------------------------------------------

class TestAskAgentWithDocuments:

    def _setup_agent(self, monkeypatch, doc_store, captured_messages):
        """Patch storage and OpenAI so we can inspect the messages sent."""
        import app.services.retrieval_service as rs
        import app.services.openai_service as oai

        monkeypatch.setattr(rs, "list_records", lambda _: doc_store.get("documents", []))
        monkeypatch.setattr(oai, "client", None)  # force local fallback

    def test_sources_returned_when_doc_matches(self, monkeypatch):
        from app.agents.pa_agent import ask_agent
        import app.services.retrieval_service as rs

        store = _make_store_with_doc("Boat hull repair scheduled for June 2026.", source_module="tasks")
        monkeypatch.setattr(rs, "list_records", lambda _: store["documents"])

        answer, sources = ask_agent("boat hull repair", use_documents=True)
        assert isinstance(answer, str)
        assert len(sources) >= 1
        assert sources[0]["filename"] == "report.txt"

    def test_no_sources_when_use_documents_false(self, monkeypatch):
        from app.agents.pa_agent import ask_agent
        import app.services.retrieval_service as rs

        store = _make_store_with_doc("Boat hull repair scheduled for June 2026.", source_module="tasks")
        monkeypatch.setattr(rs, "list_records", lambda _: store["documents"])

        answer, sources = ask_agent("boat hull repair", use_documents=False)
        assert sources == []

    def test_action_commands_still_work(self, monkeypatch):
        from app.agents.pa_agent import ask_agent
        from app.services import storage_service

        data_dir = Path("/tmp/test_williamos_actions")
        data_file = data_dir / "local_store.json"
        monkeypatch.setattr(storage_service, "DATA_DIR", data_dir)
        monkeypatch.setattr(storage_service, "DATA_FILE", data_file)

        answer, sources = ask_agent("lag oppgave Test task fra pytest", use_documents=True)
        assert "✅" in answer
        assert sources == []

    def test_openai_fallback_includes_answer(self, monkeypatch):
        from app.agents.pa_agent import ask_agent
        import app.services.openai_service as oai
        import app.services.retrieval_service as rs

        monkeypatch.setattr(oai, "client", None)
        monkeypatch.setattr(rs, "list_records", lambda _: [])

        answer, sources = ask_agent("hva er status?", use_documents=True)
        assert isinstance(answer, str)
        assert len(answer) > 0


# ---------------------------------------------------------------------------
# 5. API — documents upload persists source_module
# ---------------------------------------------------------------------------

class TestDocumentUploadAPI:
    def test_upload_stores_source_module(self, tmp_path, monkeypatch):
        from fastapi.testclient import TestClient
        from app.api.main import app
        from app.services import storage_service, document_service

        monkeypatch.setattr(storage_service, "DATA_DIR", tmp_path / ".williamos")
        monkeypatch.setattr(storage_service, "DATA_FILE", tmp_path / ".williamos" / "local_store.json")
        monkeypatch.setattr(document_service, "UPLOAD_DIR", tmp_path / "uploads")
        (tmp_path / "uploads").mkdir()

        client = TestClient(app)
        response = client.post(
            "/documents/upload",
            data={"source_module": "projects"},
            files={"file": ("notes.txt", b"Project meeting notes content", "text/plain")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["source_module"] == "projects"
        assert body["text_content"] == "Project meeting notes content"

    def test_search_endpoint(self, tmp_path, monkeypatch):
        from fastapi.testclient import TestClient
        from app.api.main import app
        from app.services import storage_service, document_service, retrieval_service

        monkeypatch.setattr(storage_service, "DATA_DIR", tmp_path / ".williamos")
        monkeypatch.setattr(storage_service, "DATA_FILE", tmp_path / ".williamos" / "local_store.json")
        monkeypatch.setattr(document_service, "UPLOAD_DIR", tmp_path / "uploads")
        (tmp_path / "uploads").mkdir()

        doc_store = _make_store_with_doc("Annual budget summary for the property portfolio.")
        monkeypatch.setattr(retrieval_service, "list_records", lambda _: doc_store["documents"])

        client = TestClient(app)
        response = client.get("/documents/search", params={"q": "budget property"})
        assert response.status_code == 200
        body = response.json()
        assert "results" in body
        assert len(body["results"]) >= 1

    def test_chat_endpoint_returns_sources(self, tmp_path, monkeypatch):
        from fastapi.testclient import TestClient
        from app.api.main import app
        from app.services import storage_service, retrieval_service
        import app.services.openai_service as oai

        monkeypatch.setattr(storage_service, "DATA_DIR", tmp_path / ".williamos")
        monkeypatch.setattr(storage_service, "DATA_FILE", tmp_path / ".williamos" / "local_store.json")
        monkeypatch.setattr(oai, "client", None)

        doc_store = _make_store_with_doc("Invoice for boat service: 15 000 NOK")
        monkeypatch.setattr(retrieval_service, "list_records", lambda _: doc_store["documents"])

        client = TestClient(app)
        response = client.post("/chat/", json={"message": "boat invoice service", "use_documents": True})
        assert response.status_code == 200
        body = response.json()
        assert "answer" in body
        assert "sources" in body
        assert len(body["sources"]) >= 1


def _make_store_with_doc(text_content: str, filename: str = "report.txt", source_module: str = "documents"):
    return {
        "documents": [
            {
                "id": "doc-001",
                "filename": filename,
                "storage_path": f"uploads/{filename}",
                "text_content": text_content,
                "source_module": source_module,
                "asset_id": None,
                "project_id": None,
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ]
    }
