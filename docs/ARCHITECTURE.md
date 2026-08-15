# WilliamOS — Architecture

## Overview

WilliamOS uses a four-layer architecture designed so the Streamlit UI can be
replaced (or supplemented) with a more custom web frontend at low cost.

```
┌─────────────────────────────────────────┐
│  UI layer  (frontend/)                  │  ← Streamlit only
│  streamlit_app.py  +  ui/  + components │
└────────────────┬────────────────────────┘
                 │ calls
┌────────────────▼────────────────────────┐
│  Service / application layer            │  ← Orchestration, no Streamlit
│  app/services/action_engine.py          │
│  app/services/memory_service.py         │
│  app/services/document_service.py       │
│  app/services/storage_service.py        │
│  app/agents/pa_agent.py                 │
│  app/agents/self_evolve.py              │
└────────────────┬────────────────────────┘
                 │ calls
┌────────────────▼────────────────────────┐
│  Infrastructure layer                   │  ← External I/O
│  app/database/supabase.py               │
│  app/services/openai_service.py         │
│  app/services/retrieval_service.py      │
│  app/services/vector_service.py         │
└─────────────────────────────────────────┘

  app/models/  — pure data models, no I/O
  app/api/     — FastAPI entrypoint (parallel to the UI layer)
```

---

## Layer responsibilities

### UI layer (`frontend/`)

| File / dir | Responsibility |
|---|---|
| `streamlit_app.py` | Page config, sidebar navigation, dispatch to page renderers |
| `ui/<page>.py` | One `render_<page>()` function per page. Streamlit widgets + calls to service layer. |
| `components/record_helpers.py` | Shared, reusable Streamlit helpers (`build_record_options`, `render_collection`) |

**Rules:**
- May import from `app/services` and `app/agents`.
- Must **not** import from `app/database` directly.
- Must **not** contain business logic (sorting, filtering, aggregation).

### Service / application layer (`app/services/`, `app/agents/`)

Orchestration functions that are UI-agnostic.  Called by Streamlit today;
could equally be called by a FastAPI handler, a CLI, or an async worker.

**Rules:**
- May import from `app/models` and `app/database`.
- Must **not** import `streamlit`.
- Should not import from `frontend/`.

### Infrastructure layer (`app/database/`, `app/services/openai_service.py`, …)

Thin wrappers around external services (Supabase, OpenAI).  All external I/O
lives here.

**Rules:**
- No business logic.
- No Streamlit imports.
- Should raise clear `RuntimeError` when not configured (see `storage_service.py`).

### Models (`app/models/`)

Pure Python dataclasses / type hints.  No I/O, no Streamlit.

---

## Import direction rules

```
frontend/ → app/services/ → app/database/
frontend/ → app/agents/  → app/services/
app/models/ ← (all layers may import)
```

Imports must only flow **downward**.  If you find yourself importing a higher
layer from a lower one, extract the shared concern into `app/models/` or a
new service.

---

## How to add a new feature

1. **Data / logic first** — add a function in `app/services/action_engine.py`
   (or a new service file) that handles the business logic with no Streamlit
   imports.

2. **Tests** — add a test in `tests/` that exercises the service function
   using the `_make_fake_supabase` / `_patch_supabase` helpers.

3. **UI last** — add a new `frontend/ui/<feature>.py` file with a single
   `render_<feature>()` function that calls the service function and presents
   results via Streamlit widgets.

4. **Wire up** — import and register `render_<feature>` in
   `frontend/streamlit_app.py`'s `_PAGE_RENDERERS` dict.

When a future web frontend is built (e.g. with React + FastAPI):
- Steps 1–2 remain identical.
- Step 3 becomes a React component + FastAPI route instead of a Streamlit page.
- The service layer is **not touched**.

---

## Follow-up suggestions for UI modernisation

- Replace `st.dataframe` tables with card-style layouts using `st.columns` +
  `st.container` for a less "Excel-like" feel.
- Add a custom CSS block in `streamlit_app.py` for consistent typography,
  spacing, and dark-mode polish.
- Consider migrating to a FastAPI + React (or Next.js) frontend using the
  existing service layer as the API backend — the refactored structure makes
  this straightforward.
- Introduce Pydantic models in `app/models/` for request/response validation
  once the FastAPI surface grows.
