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
                "storage_path": f"documents/{filename}",
                "text_content": text_content,
                "source_module": source_module,
                "asset_id": None,
                "project_id": None,
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ]
    }


def _make_fake_supabase(records_by_collection: dict | None = None):
    """Build a minimal in-memory Supabase stub that supports CRUD + Storage."""
    store = records_by_collection if records_by_collection is not None else {}
    bucket_store: dict[str, dict[str, bytes]] = {}

    class _Query:
        def __init__(self, collection):
            self._collection = collection
            self._filters = {}
            self._op = None
            self._payload = None
            self._order_desc = False

        def select(self, _fields="*"):
            self._op = "select"
            return self

        def insert(self, payload):
            self._op = "insert"
            self._payload = payload
            return self

        def eq(self, field, value):
            self._filters[field] = value
            return self

        def order(self, _col, desc=False):
            self._order_desc = desc
            return self

        def limit(self, _count):
            return self

        def execute(self):
            rows = store.setdefault(self._collection, [])
            if self._op == "select":
                result = [r for r in rows if all(r.get(k) == v for k, v in self._filters.items())]
                if self._order_desc:
                    result = sorted(result, key=lambda r: r.get("created_at", ""), reverse=True)
                return type("R", (), {"data": result})()
            if self._op == "insert":
                rows.append(self._payload)
                return type("R", (), {"data": [self._payload]})()
            return type("R", (), {"data": []})()

    class _Bucket:
        def __init__(self, name):
            self._name = name

        def upload(self, *, path, file, file_options=None):
            bucket_store.setdefault(self._name, {})[path] = file
            return {"path": path, "file_options": file_options or {}}

        def download(self, path):
            return bucket_store[self._name][path]

        def list(self, path=""):
            return [
                {"name": object_path.rsplit("/", 1)[-1], "path": object_path}
                for object_path in sorted(bucket_store.get(self._name, {}))
                if not path or object_path.startswith(path)
            ]

        def remove(self, paths):
            bucket = bucket_store.setdefault(self._name, {})
            for object_path in paths:
                bucket.pop(object_path, None)
            return {"paths": paths}

    class _Storage:
        def from_(self, bucket):
            return _Bucket(bucket)

    class _FakeClient:
        def __init__(self):
            self.storage = _Storage()

        def table(self, name):
            return _Query(name)

    client = _FakeClient()
    client.bucket_store = bucket_store
    return client


def _set_test_context() -> None:
    from app.services.auth_context import UserContext, set_current_context

    set_current_context(
        UserContext(
            user_id="user-test",
            email="test@example.com",
            household_id="household-test",
            access_token="",
            refresh_token="",
        )
    )


def _patch_supabase(monkeypatch, fake_client=None):
    client = fake_client if fake_client is not None else _make_fake_supabase()
    from app.services import document_storage, storage_service
    from app.services.auth_context import UserContext, set_current_context

    set_current_context(
        UserContext(
            user_id="user-test",
            email="test@example.com",
            household_id="household-test",
            access_token="test-access-token",
            refresh_token="test-refresh-token",
        )
    )
    monkeypatch.setattr(storage_service, "get_client", lambda: client)
    monkeypatch.setattr(document_storage, "get_client", lambda: client)
    return client


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
    def test_returns_text_content_for_text_file(self, monkeypatch):
        from app.services import document_storage

        fake_client = _patch_supabase(monkeypatch)
        _set_test_context()
        monkeypatch.delenv("DOCUMENTS_BUCKET", raising=False)

        result = document_storage.save_uploaded_file("hello.txt", b"Budget: 100 NOK")
        assert result["text_content"] == "Budget: 100 NOK"
        assert result["filename"] == "hello.txt"
        assert result["storage_path"].startswith("household/household-test/")
        assert fake_client.bucket_store["documents"][result["storage_path"]] == b"Budget: 100 NOK"

    def test_returns_none_text_for_binary(self, monkeypatch):
        from app.services import document_storage

        _patch_supabase(monkeypatch)
        result = document_storage.save_uploaded_file("photo.jpg", bytes(range(256)))
        assert result["text_content"] is None

    def test_read_list_and_delete_use_supabase_storage(self, monkeypatch):
        from app.services import document_storage

        fake_client = _patch_supabase(monkeypatch)
        _set_test_context()
        saved = document_storage.save_uploaded_file("notes.txt", b"Stored in bucket", source_module="projects")

        assert document_storage.read_document_text(saved["storage_path"], saved["filename"]) == "Stored in bucket"
        assert document_storage.list_document_objects("household/household-test/projects")[0]["path"] == saved["storage_path"]

        document_storage.delete_document(saved["storage_path"])
        assert fake_client.bucket_store["documents"] == {}

    def test_missing_supabase_config_raises(self, monkeypatch):
        from app.services import document_storage, storage_service

        monkeypatch.setattr(storage_service, "get_client", lambda: None)
        monkeypatch.setattr(document_storage, "get_client", lambda: None)

        with pytest.raises(RuntimeError, match="Supabase is not configured"):
            document_storage.save_uploaded_file("hello.txt", b"Budget: 100 NOK")

    def test_invalid_bucket_config_raises(self, monkeypatch):
        from app.services import document_storage

        _patch_supabase(monkeypatch)
        monkeypatch.setenv("DOCUMENTS_BUCKET", "   ")

        with pytest.raises(RuntimeError, match="DOCUMENTS_BUCKET is misconfigured"):
            document_storage.save_uploaded_file("hello.txt", b"Budget: 100 NOK")

    def test_supabase_storage_errors_propagate(self, monkeypatch):
        from app.services import document_storage, storage_service

        class _BrokenBucket:
            def upload(self, **_kwargs):
                raise RuntimeError("storage unavailable")

        class _BrokenStorage:
            def from_(self, _bucket):
                return _BrokenBucket()

        class _BrokenClient:
            storage = _BrokenStorage()

        monkeypatch.setattr(storage_service, "get_client", lambda: _BrokenClient())
        monkeypatch.setattr(document_storage, "get_client", lambda: _BrokenClient())

        with pytest.raises(RuntimeError, match="storage unavailable"):
            document_storage.save_uploaded_file("hello.txt", b"Budget: 100 NOK")


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

    def _patch_agent_deps(self, monkeypatch, doc_store=None):
        import app.agents.pa_agent as pa
        import app.services.openai_service as oai
        import app.services.retrieval_service as rs

        monkeypatch.setattr(pa, "log_request", lambda request_text: None)
        monkeypatch.setattr(pa, "get_recent_memory_text", lambda limit=20: "")
        monkeypatch.setattr(pa, "get_assistant_name", lambda: "WilliamOS")
        monkeypatch.setattr(oai, "client", None)
        documents = doc_store.get("documents", []) if doc_store else []
        monkeypatch.setattr(rs, "list_records", lambda _: documents)

    def test_sources_returned_when_doc_matches(self, monkeypatch):
        from app.agents.pa_agent import ask_agent

        store = _make_store_with_doc("Boat hull repair scheduled for June 2026.", source_module="tasks")
        self._patch_agent_deps(monkeypatch, store)

        answer, sources = ask_agent("boat hull repair", use_documents=True)
        assert isinstance(answer, str)
        assert len(sources) >= 1
        assert sources[0]["filename"] == "report.txt"

    def test_no_sources_when_use_documents_false(self, monkeypatch):
        from app.agents.pa_agent import ask_agent

        store = _make_store_with_doc("Boat hull repair scheduled for June 2026.", source_module="tasks")
        self._patch_agent_deps(monkeypatch, store)

        answer, sources = ask_agent("boat hull repair", use_documents=False)
        assert sources == []

    def test_action_commands_still_work(self, monkeypatch):
        from app.agents.pa_agent import ask_agent
        _patch_supabase(monkeypatch)

        answer, sources = ask_agent("lag oppgave Test task fra pytest", use_documents=True)
        assert "✅" in answer
        assert sources == []

    def test_openai_fallback_includes_answer(self, monkeypatch):
        from app.agents.pa_agent import ask_agent

        self._patch_agent_deps(monkeypatch)

        answer, sources = ask_agent("hva er status?", use_documents=True)
        assert isinstance(answer, str)
        assert len(answer) > 0


# ---------------------------------------------------------------------------
# 5. API — documents upload persists source_module
# ---------------------------------------------------------------------------

class TestDocumentUploadAPI:
    def test_upload_stores_source_module(self, monkeypatch, authed_client):
        fake_client = _patch_supabase(monkeypatch)
        _set_test_context()

        response = authed_client.post(
            "/documents/upload",
            data={"source_module": "projects"},
            files={"file": ("notes.txt", b"Project meeting notes content", "text/plain")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["source_module"] == "projects"
        assert body["text_content"] == "Project meeting notes content"
        assert body["storage_path"].startswith("household/household-test/projects/")
        assert fake_client.bucket_store["documents"][body["storage_path"]] == b"Project meeting notes content"

    def test_search_endpoint(self, monkeypatch, authed_client):
        from app.services import retrieval_service

        _patch_supabase(monkeypatch)

        doc_store = _make_store_with_doc("Annual budget summary for the property portfolio.")
        monkeypatch.setattr(retrieval_service, "list_records", lambda _: doc_store["documents"])

        response = authed_client.get("/documents/search", params={"q": "budget property"})
        assert response.status_code == 200
        body = response.json()
        assert "results" in body
        assert len(body["results"]) >= 1

    def test_chat_endpoint_returns_sources(self, monkeypatch, authed_client):
        from app.agents import pa_agent
        from app.services import retrieval_service
        import app.services.openai_service as oai

        _patch_supabase(monkeypatch)
        monkeypatch.setattr(oai, "client", None)
        monkeypatch.setattr(pa_agent, "log_request", lambda request_text: None)
        monkeypatch.setattr(pa_agent, "get_assistant_name", lambda: "WilliamOS")
        monkeypatch.setattr(pa_agent, "get_recent_memory_text", lambda limit=20: "")

        doc_store = _make_store_with_doc("Invoice for boat service: 15 000 NOK")
        monkeypatch.setattr(retrieval_service, "list_records", lambda _: doc_store["documents"])

        response = authed_client.post("/chat", json={"message": "boat invoice service", "use_documents": True})
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
                "storage_path": f"documents/{filename}",
                "text_content": text_content,
                "source_module": source_module,
                "asset_id": None,
                "project_id": None,
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ]
    }
