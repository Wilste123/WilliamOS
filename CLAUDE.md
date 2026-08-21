# Claude briefing — WilliamOS / Mini-jarv

Read this first. Then read [`docs/PROJECT-PRESENTATION.md`](docs/PROJECT-PRESENTATION.md) for the full product, vision, domain, and architecture briefing.

This file is the working contract for coding agents.

---

## What this is

A **personal Chief of Staff**, not a chatbot.

Internal names: **WilliamOS** (platform) → **HouseOS** (first commercial wedge) → **LifeOS** (long-term OS for everything people own). The PWA brand the user sees is **Mini-jarv**.

North star question the product must answer: **"Hva bør jeg gjøre denne uka?"**

We are not building ChatGPT with extra buttons. AI must **propose and execute structured actions** (tasks, assets, documents, calendar) after user confirmation.

---

## Non-negotiable rules

1. **Python is the brain. Next.js is only the interface.**
2. Frontend never calls OpenAI, Postgres, or Supabase Storage for app data. Auth session on the client is the only exception.
3. All mutations go through the **Action Engine** (`app/services/action_engine.py`) or `execute_chat_action` (`app/services/action_executor.py`). AI never writes storage directly.
4. Mutating chat tools are **proposal-mode**: show a confirmation card, then `POST /actions/execute`. Inbox capture, memory, and complete_task may run immediately.
5. UI copy is **Norwegian**. Code, comments, commits, and most docs are **English**.
6. Do not add Streamlit. Do not add Next.js API routes for business logic. FastAPI is the only backend.
7. Every user-owned row is scoped with `user_id`, `household_id`, `visibility` (`private` | `household`). RLS must stay intact.
8. New features: domain/service → tests → FastAPI → Next.js. Never UI-first with logic in React.
9. Prefer simplifying a daily-use loop over adding a new module. User #0 (William) must use this daily before HouseOS beta.

---

## Stack and traffic path

```
web/ (Next.js 15 PWA)  →  /api/* rewrite  →  FastAPI (app/api/)  →  services/agents  →  Supabase + OpenAI
```

| Layer | Path | Role |
|-------|------|------|
| UI | `web/` | Next.js 15, React 19, Tailwind, shadcn, dark mobile-first PWA |
| API | `app/api/` | FastAPI, JWT auth middleware, OpenAPI at `/docs` |
| Brain | `app/services/`, `app/agents/` | Action Engine, PA agent, briefs, retrieval |
| Domain | `app/models/` | Pydantic types, no I/O |
| Data | `migrations/`, `app/database/` | Supabase Postgres + Auth + Storage + pgvector |
| PA prompt | `prompts/pa_system_prompt.txt` | Norwegian, action-oriented |

Local: FastAPI `:8000`, Next `:3000`. Browser calls `/api/*`; Next rewrites to FastAPI (`API_PROXY_URL`, default `http://127.0.0.1:8000`).

---

## Daily-use modules (do not invent new top-level nav without product reason)

Primary (bottom bar): **Hjem, Chat, Inbox, Oppgaver**, plus **Mer**.

| Route | Purpose |
|-------|---------|
| `/home` | Greeting, net worth, weekly brief, daily proposals, priorities |
| `/chat` | Streaming PA, yellow action cards, missions (`oppdrag:`) |
| `/inbox` | Capture → AI suggestions → apply |
| `/tasks` | Tasks linked to assets/projects |
| `/assets` | Asset-first: bolig, hytte, bil, båt, other + detail timeline |
| `/projects` `/goals` `/decisions` `/documents` `/calendar` `/timeline` | Life modules |
| `/finance` `/health` | Thin modules exist; not the current wedge |
| `/memory` `/integrations` `/settings` | PA context, Google, export, 7-day usage |
| `/self-evolve` | Dev-only, not in nav |

---

## How to add a feature

1. Types in `app/models/` (and constants in `app/constants/` if shared).
2. Logic in `app/services/` (mutations via Action Engine).
3. Tests in `tests/` with fake Supabase helpers from `tests/conftest.py`.
4. FastAPI route in `app/api/routes/` — handler only delegates.
5. UI in `web/src/app/(app)/` calling `web/src/lib/api.ts`.

If the PA should do it: add a tool in `app/agents/pa_agent.py`, map it in `chat_actions.py` / `action_executor.py`, update `prompts/pa_system_prompt.txt`.

---

## Commands

```bash
# API
uvicorn app.api.main:app --reload --port 8000

# Web
cd web && npm run dev

# Tests
python3 -m pytest tests/ -q
```

Full product context: **[docs/PROJECT-PRESENTATION.md](docs/PROJECT-PRESENTATION.md)**  
Architecture: `docs/ARCHITECTURE.md` + `docs/ARCHITECTURE-vision.md`  
Vision sources: `docs/PRODUCT-VISION.md`, `docs/ENDGOAL.md`, `MVP-FOCUS.md`
