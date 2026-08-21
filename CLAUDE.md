# CLAUDE.md — WilliamOS / Mini-jarv

Read this first. For the full briefing (vision, modules, AI engine, data model, roadmap), read **[docs/PROJECT-PRESENTATION.md](docs/PROJECT-PRESENTATION.md)**.

You are working on **WilliamOS**, branded in the PWA as **Mini-jarv**. It is a personal Chief of Staff — not a chatbot, not a task manager, not a dashboard.

Lineage: **WilliamOS** (this repo, User #0 prototype) → **HouseOS** (first paid product: home PA) → **LifeOS** (life operating system).

---

## Hard rules

1. **Python is the brain. React is only the interface.**
2. Frontend never calls OpenAI, Supabase data, or Storage directly. Auth session in the browser is allowed; all CRUD/AI goes through FastAPI.
3. **AI suggests. Action Engine executes.** Mutating chat tools require user confirmation (proposal cards) except capture/memory/complete-task.
4. AI must **do**, not only advise. Bad: “You should create a task.” Good: a yellow action card the user can confirm.
5. Every feature must improve **overview, prioritization, or decisions**. If it does not, it probably does not belong.
6. **Asset-first.** Tasks, documents, costs, events, and decisions hang off assets (house, cabin, car, boat).
7. **Inbox is the capture surface.** Unstructured input lands there and becomes structured objects.
8. UI language is **Norwegian**. Code, APIs, and docs for agents are English unless editing user-facing copy.
9. Do not add Økonomi/Helse depth, App Store / Capacitor, or marketing until User #0 (William) uses Mini-jarv daily. See `docs/HOUSEOS-BETA.md`.
10. Do not revive Streamlit. Production UI is Next.js only. Older docs that mention Streamlit as current are stale.

---

## Stack (current)

```
web/ (Next.js 15 PWA)  →  FastAPI (app/api/)  →  app/services + app/agents  →  Supabase / OpenAI
```

| Layer | Path | Role |
|-------|------|------|
| UI | `web/` | Display, forms, chat, PWA. Calls `/api/*` (proxied to FastAPI). |
| API | `app/api/` | JWT auth, Pydantic contracts, SSE chat. No business logic in routes. |
| Application | `app/services/`, `app/agents/` | Action Engine, PA agent, briefs, integrations. |
| Domain | `app/models/` | Pure types. No I/O. |
| Infra | `app/database/`, OpenAI, Google | External I/O only. |
| Schema | `migrations/` | Run in order in Supabase SQL editor. |
| Tests | `tests/` | Hit services with fake Supabase helpers. |

---

## How to add a feature

1. Types in `app/models/` + logic in `app/services/` (or Action Engine). No React.
2. Tests in `tests/`.
3. FastAPI route with Pydantic models; handler delegates to a service.
4. Next.js page/component in `web/` calling `web/src/lib/api.ts`.
5. Never put business logic, OpenAI, or Supabase queries in frontend code.

---

## Daily-use modules (Norwegian UI)

Primary nav: **Hjem · Chat · Inbox · Oppgaver**. Everything else is under **Mer**.

Hjem, Chat, Inbox, Oppgaver, Eiendeler, Økonomi, Helse, Mål, Prosjekter, Beslutninger, Dokumenter, Kalender, Historikk, Integrasjoner, Minne, Innstillinger.

Brand name in UI: Mini-jarv (assistant_name is user-configurable).

---

## Local run

```bash
# terminal 1
uvicorn app.api.main:app --reload --port 8000
# terminal 2
cd web && npm run dev
```

http://localhost:3000 · API docs http://localhost:8000/docs · tests: `python3 -m pytest tests/ -q`

---

## Key files

| File | Why |
|------|-----|
| `docs/PROJECT-PRESENTATION.md` | Full product + architecture briefing |
| `docs/PRODUCT-VISION.md` | LifeOS mission (Norwegian) |
| `docs/ENDGOAL.md` | Target product spec |
| `docs/ARCHITECTURE.md` | Developer architecture (current) |
| `MVP-FOCUS.md` | What “done” means for daily use |
| `app/services/action_engine.py` | All mutations + briefs/priorities |
| `app/agents/pa_agent.py` | Tool-calling PA |
| `app/services/chat_actions.py` | Proposal vs execute |
| `prompts/pa_system_prompt.txt` | PA personality |
| `web/src/lib/navigation.ts` | Nav + brand |
| `web/src/lib/api.ts` | Frontend API client |
