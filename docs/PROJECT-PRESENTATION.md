# WilliamOS — Project Presentation for Claude

This is the canonical briefing for AI coding assistants (Claude, Cursor, etc.). Read it before changing code.

Shorter operating rules live in [`CLAUDE.md`](../CLAUDE.md). Older docs are still valid for depth, but **this file wins on current state** if they disagree (especially anything that still treats Streamlit as the production UI).

---

## 1. What we are building

**WilliamOS** is a personal Chief of Staff.

It is not a chatbot. It is not a to-do app. It is not a dashboard that you stare at.

It is a **personal operating system**: one place that understands what you own, what you owe, what you decided, and what you should do next — then **executes** (with your confirmation) instead of only talking.

Public PWA name: **Mini-jarv**. Internal / repo name: **WilliamOS**. Founder: **William Berg Steffenak**, Trondheim.

The product question, every day:

> “What should I focus on right now?” / “Hva bør jeg gjøre denne uka?”

If a feature does not help the user **understand, prioritize, act, or learn**, it probably does not belong.

---

## 2. Vision ladder

```
WilliamOS  →  HouseOS  →  LifeOS
(this repo)   (first paid wedge)   (category)
```

### WilliamOS (now)

Internal prototype. User #0 is William. Goal: he uses Mini-jarv daily for capture, tasks, assets, chat, and the weekly brief — **without reaching for Notes or a discarded prototype UI**.

### HouseOS (next commercial product)

Same backend, narrower story: **“your house PA.”**

Problem: nobody has their home organized. Documents, maintenance, insurance, and tasks live in email, folders, and memory.

HouseOS gathers:

- documents
- maintenance
- insurance
- tasks
- history
- costs

Target: homeowners who also have a cabin or boat (already modeled as assets). Beta: 3–5 friends/family at **99 kr/mnd** after William himself is a daily driver. See [`HOUSEOS-BETA.md`](HOUSEOS-BETA.md).

### LifeOS (long-term category)

**The operating system for everything people own, maintain, and decide about.**

Today that information is scattered across folders, email, banks, insurers, spreadsheets, note apps, and the user’s head. LifeOS is one system.

Analogies the product uses internally:

| Company | Organizes |
|---------|-----------|
| Apple | Digital devices |
| Microsoft | Work |
| Google | Information |
| **LifeOS** | **Life** |

Planned LifeOS modules (not all built as products yet):

- HouseOS
- VehicleOS
- CabinOS
- FinanceOS
- FamilyOS
- Future modules (health, learning, life transitions)

North star: the user can ask “Hva bør jeg gjøre denne uka?” and get a **correct** answer grounded in their structured life data.

---

## 3. Mission, north star, success

**Mission:** Help people organize, understand, and make better decisions about everything they own.

**Loop:** Understand → Prioritize → Act → Learn.

**North star feature:** the **Priority Engine**. It should weigh tasks, goals, projects, documents, assets, inbox, email signals, and calendar — then return a ranked list of what matters this week.

**Success metric:** days per week the user opens the app. Target **5+**. Retention beats feature count.

**Moat:** not the chat UI. The **structured life history**:

- assets with timelines
- documents linked to homes/vehicles
- decisions with context
- auto-generated events on every mutation

Every week of use makes switching harder.

**Monetization (vision, not implemented in-app):**

| Plan | Price |
|------|-------|
| Person | 99 kr/mnd |
| Familie | 199 kr/mnd |
| Premium | 299 kr/mnd |

HouseOS beta starts at 99 kr/mnd (Vipps/faktura — no App Store required).

---

## 4. What this product is not

Do not steer the codebase toward:

- a generic ChatGPT wrapper
- an ERP / CRM / Excel feeling
- a second native UI codebase
- a dumping ground for unrelated life-tracking widgets

Design references: **Apple, Linear, Arc, ChatGPT Mobile**. Dark mode, cards, mobile-first, calm, minimal.

---

## 5. Product principles (non-negotiable)

### Rule 1 — AI executes, it does not only answer

Bad: “Du burde opprette en oppgave.”

Good: yellow confirmation card → user taps **Utfør** → “Oppgave opprettet.”

Mutating tools go through **proposal mode**. The model calls a tool; the UI shows a card; FastAPI `POST /actions/execute` runs `action_executor` → Action Engine. AI never writes storage directly.

Immediate (no card) on purpose: inbox capture, save memory, complete task.

### Rule 2 — Everything is structured data

Inbox text, chat, PDFs, Gmail snippets, and calendar events become **objects**: Asset, Task, Project, Document, Event, Decision, Goal, Memory, CalendarEvent.

Users should not think in folders.

### Rule 3 — Asset-first

Life is modeled around things you own.

Example: **Mazda CX-5** has tasks, documents, history, costs, events, decisions. Same pattern for a house, cabin, or boat.

Asset types in code: `vehicle`, `boat`, `property`, `cabin`, `other` (UI: Bil, Båt, Bolig, Hytte, Annet).

Statuses: `active` | `considering_purchase` | `inactive`.

### Rule 4 — Inbox is the front door

Everything unstructured starts in Inbox.

Example:

> “Vurderer å kjøpe Pioner 320 til 25 000”

System should propose:

- Asset: Pioner 320
- Value: 25 000
- Status: considering_purchase

User accepts or ignores. Document intelligence works the same way (“Is this the new insurance for Mazda CX-5?”).

### Rule 5 — Feature filter

Every feature must support better **overview**, **prioritization**, or **decisions**.

---

## 6. Current phase (honest)

This is a **working prototype / daily-use MVP**, not a launched company product.

| True today | Not true yet |
|------------|----------------|
| Next.js PWA is the only client | Streamlit is gone from the repo; ignore stale “Streamlit is current UI” notes |
| FastAPI is the public API | Generated TypeScript client / full OpenAPI-driven frontend |
| Households + RLS + JWT | Multi-user family product polish |
| Chat with tool calling + proposal cards | Perfect priority engine |
| Google Calendar + Gmail → inbox | Banks, Apple Health, Garmin, Outlook as live feeds |
| Manual finance accounts + health metrics | Automatic net-worth from banks |
| Self-evolve is a keyword logger | Self-evolve as a feature factory |
| Brand Mini-jarv | HouseOS public launch |

**Current gate:** William uses Mini-jarv daily for **7 days** (`docs/SEVEN-DAY-TEST.md`). If he does not, **simplify** — do not add modules.

After 5+ days/week for ~30 days → deploy + HouseOS beta. Do **not** build deeper Økonomi/Helse, App Store, or marketing before that.

---

## 7. Brand, language, user #0

- UI copy: **Norwegian** (bokmål).
- Assistant default name: Mini-jarv (user can rename in Innstillinger / onboarding).
- PA answers in Norwegian by default (`prompts/pa_system_prompt.txt`).
- Tone: direct, practical, concrete. Never vague.
- Example real-world assets in product docs: Lademoen, Tun32, Skarnsundet, Mazda CX-5, Pioner 320.
- Data residency story the PA is allowed to mention: Supabase `eu-north-1` (Stockholm), GDPR-aligned; app founded by William in Trondheim.

Onboarding (`/onboarding`) seeds memory: primary use (home / work / finance / general), assets mentioned (bolig, hytte, båt, bil), current focus, assistant name.

---

## 8. Product surface (what the user sees)

Routes live under `web/src/app/(app)/`. Nav is `web/src/lib/navigation.ts`.

**Bottom bar (daily driver):** Hjem, Chat, Inbox, Oppgaver.  
**Mer menu:** remaining life + system modules.  
**Not in nav:** `/self-evolve` (dev), `/dashboard` → redirects to `/home`, `/events` → `/timeline`.

| Module | Route | Purpose (today) |
|--------|-------|-----------------|
| Hjem | `/home` | Greeting, net worth, open tasks, priorities, weekly brief, daily brief with **executable proposals** (overdue tasks, inbox suggestions, upcoming calendar). |
| Chat | `/chat` | Streaming PA, persistent history, yellow action cards, document source chips, `oppdrag:` missions. |
| Inbox | `/inbox` | Capture raw text → LLM/rule suggestions → apply or dismiss. Gmail unread can land here. |
| Oppgaver | `/tasks` | Create, complete, edit. Link to asset/project. Priority 1–3. |
| Eiendeler | `/assets`, `/assets/[id]` | CRUD + detail: linked tasks, docs, timeline, value. Drives Hjem net worth. |
| Økonomi | `/finance` | Manual accounts (asset / debt / liquidity), snapshots, net worth + 12m change. Asset values roll in. |
| Helse | `/health` | Manual metrics (weight, sleep, activity). Goals can link to health. No Apple/Garmin yet. |
| Mål | `/goals`, `/goals/[id]` | Progress 0–100, next step, module (`health`, `finance`, `asset`, `project`, `general`) + `linked_id`. |
| Prosjekter | `/projects`, `/projects/[id]` | Status active/on_hold/done, next_action, links to assets/goals/docs/tasks/decisions/finance. |
| Beslutninger | `/decisions` | open / decided / paused + summary + next_action. |
| Dokumenter | `/documents` | Upload to Supabase Storage, text extract, intelligence → inbox, embeddings for semantic search. |
| Kalender | `/calendar` | Internal events + Google sync (two-way when connected). |
| Historikk | `/timeline` | Auto events from Action Engine (asset created, task updated, …). |
| Integrasjoner | `/integrations` | Google OAuth (Calendar write + Gmail). |
| Minne | `/memory` | Durable facts injected into PA context. |
| Innstillinger | `/settings` | Profile, assistant name, export, usage / 7-day test stats. |
| Login / onboarding | `/login`, `/onboarding` | Supabase email auth; questionnaire seeds memory. |

Hjem should answer “what matters this week?” If it does not, fix the brief/priority engine — do not add another dashboard.

---

## 9. Core loop (how the product is supposed to feel)

**Morning (2 min):** Open Hjem → read ukens brief + Mini-jarv proposals → tap **Utfør** on 1–3 items, or tap a priority into Chat.

**During the day:** Capture in Inbox or chat (`fang i innboks …`). Complete tasks. Ask the PA; confirm action cards.

**Missions:** `oppdrag: Forbered hyttetur neste helg` → planner returns a multi-step proposal plan → confirm each or “Utfør alle”.

**Evening:** Process one inbox card. Ask “Hva bør jeg gjøre i morgen?”

**Documents:** Upload insurance PDF → later ask “Hva står om taket i hytteforsikringen?” Hybrid search (embeddings + keywords) + citations.

---

## 10. AI engine (the brain)

All of this is Python. The model is a tool-caller sitting on top of the Action Engine.

### Personal assistant

- `app/agents/pa_agent.py` — OpenAI function calling, streaming.
- `prompts/pa_system_prompt.txt` — personality and rules.
- Daily chat model: `OPENAI_MODEL` (default `gpt-4o-mini`).
- Planner / hard missions: `OPENAI_MODEL_PLANNER` (default `gpt-4o`).
- Embeddings: `OPENAI_EMBEDDING_MODEL` (default `text-embedding-3-small`).

Context packed into the prompt: profile/onboarding, memory, entity graph, retrieved document chunks, chat history, intent hint (`app/agents/intent_router.py`).

Self-evolve (`app/agents/self_evolve.py`) currently **logs chat requests** and counts keywords. It is a **motor for later**, not a product surface. Do not expand it until the daily loop is solid.

### Tools the model can call

Mutating (proposal cards): create/update/delete **asset, task, project, decision, goal, calendar event**; `create_document`; `apply_inbox_suggestion`.

Immediate: `capture_inbox`, `save_memory`, `complete_task`, plus read-only: list_*, `get_priority_focus`, `get_weekly_brief`, `search_documents`, `web_search` (Serper), `list_upcoming_schedule`, `sync_google_calendar`.

### Proposal pipeline

1. Model emits a tool call.
2. `chat_actions.PROPOSE_TOOLS` → card `status: proposed` (UI: yellow).
3. User confirms → `POST /actions/execute` or batch.
4. `action_executor.execute_chat_action` → Action Engine function.
5. Action Engine writes via `storage_service` and **appends a timeline event**.

Missions: `POST /missions/plan` or chat prefix `oppdrag:` / `mission:`. LLM planner with a rule-based fallback (`mission_service.py`).

### Proactive Chief of Staff

`GET /daily-brief` (`brief_service.py`) builds executable proposals from:

- unprocessed inbox suggestions
- overdue tasks
- upcoming calendar prep

Shown on Hjem as “Forslag fra Mini-jarv”.

`GET /weekly-brief` and `GET /priorities` / `GET /home` come from Action Engine.

---

## 11. Architecture

**Core principle: UI is disposable. The Python backend is the brain.**

```
iPhone PWA / Browser / (later Capacitor, voice)
              │
              ▼
     Next.js (web/)  — Tailwind, shadcn-style UI, mobile-first
              │  Bearer JWT + refresh header; /api/* rewrite → FastAPI
              ▼
     FastAPI (app/api/)  — auth middleware, OpenAPI, SSE
              │
              ▼
     Services + agents  — orchestration, Action Engine, PA
              │
              ▼
     Domain models (app/models/)  — no I/O
              │
              ▼
     Infrastructure — Supabase Postgres/Auth/Storage, OpenAI, Google, Serper
```

### Import rules (downward only)

Allowed:

- `web/` → FastAPI over HTTP only
- `app/api/` → services, agents, models
- `app/services/` → models, database, infra
- `app/agents/` → services, models
- `app/database/` → Supabase / external SDKs

Forbidden:

- frontend → OpenAI or Supabase data/storage
- Next.js API routes that contain business logic (the `/api` rewrite is a **proxy**, not an app backend)
- services → React
- models → I/O, FastAPI, OpenAI

### Auth and tenancy

1. Browser signs in with **Supabase Auth** (email).
2. Access token sent as `Authorization: Bearer`. Refresh token as `X-Refresh-Token`.
3. FastAPI middleware builds `UserContext` (user_id, household_id, display name).
4. `storage_service` scopes every query. JWT is also what Postgres RLS sees.

Every user-owned row:

- `user_id`
- `household_id` (optional)
- `visibility`: `private` | `household`

Defaults: household for assets/tasks/projects/docs/decisions/events/goals/finance; **private** for inbox, memory, chat, health, usage.

Households: `households` + `household_members` (owner/member). Profile: `user_profiles` (display_name, assistant_name, preferences JSON, default household).

Transparency requirement (vision): user can view, edit, export, and delete everything WilliamOS knows. Export exists in settings; keep this door open when adding tables.

### Mobile strategy

Do **not** build a separate native app.

```
Next.js → PWA (Add to Home Screen) → Capacitor later if traction
```

iPhone testing: ngrok **port 3000 only**. Next.js rewrites `/api/*` to FastAPI on the machine. Never set `NEXT_PUBLIC_API_URL=http://localhost:8000` for phone tests.

### Deploy (after 7-day gate)

- `web/` → Vercel
- FastAPI → Fly.io (EU), `CORS_ORIGINS` = Vercel URL
- Supabase → `eu-north-1`
- Google production redirect + Fly secrets via `scripts/deploy-fly.sh`

See [`DEPLOY.md`](DEPLOY.md).

---

## 12. Data model (domain objects)

These are the nouns of LifeOS. Link them; do not invent parallel silos.

| Object | Table / collection | Role |
|--------|-------------------|------|
| Asset | `assets` | House, cabin, car, boat, other. Value feeds net worth. |
| Task | `tasks` | Actionable work. `priority` 1–3, status open/in_progress/completed. |
| Project | `projects` | Multi-step work; `next_action`; optional `asset_id`. |
| Project links | `project_links` | Join to asset/goal/document/finance_account/task/decision. |
| Goal | `goals` | Outcome with progress + next_step + module + linked_id. |
| Document | `documents` | File in Storage + `text_content` + optional embedding. |
| Decision | `decisions` | Choice with reasoning/summary; status open/decided/paused. |
| Event | `events` | Automatic life/audit timeline. |
| Calendar event | `calendar_events` | User schedule; optional Google id. |
| Inbox item | `inbox_items` | Raw capture + JSON suggestions. |
| Memory | `memory_items` | Durable PA facts. |
| Chat history | `chat_history` | Session continuity. |
| Finance account | `finance_accounts` | asset / debt / liquidity balances (NOK). |
| Finance snapshot | `finance_snapshots` | Point-in-time net worth. |
| Health metric | `health_metrics` | Manual (and later connected) vitals. |
| Usage log | `usage_log` | app_opened etc. for 7-day test. |
| Integrations | `user_integrations` | OAuth tokens (Google). |
| Requests log | `requests_log` | Self-evolve signals. |
| Household | `households`, `household_members`, `user_profiles` | Auth graph. |

Action Engine helpers (mutations should go through these so timeline events are written):

`create_asset`, `update_asset`, `create_task`, `update_task`, `create_project`, `create_document`, `create_event`, `create_decision`, `create_goal`, plus inbox apply/dismiss, briefs, timeline, priority engine.

---

## 13. Backend map

```
app/
  api/                 FastAPI app, middleware, routes
    main.py            Router mount + CORS + health
    middleware/        JWT → UserContext
    routes/            One module per resource
  agents/
    pa_agent.py        Tool schemas + execution loop
    intent_router.py   Cheap context hints
    self_evolve.py     Request logging
  services/            Brain
    action_engine.py   Mutations + home/brief/priority/timeline
    action_executor.py Chat card → engine
    chat_actions.py    Proposal cards
    brief_service.py   Daily executable proposals
    mission_service.py Multi-step plans
    storage_service.py Scoped CRUD
    document_*.py      Upload, intelligence, embeddings
    retrieval_service.py Hybrid document search
    calendar_service.py Internal + Google writeback
    google_service.py  OAuth + Calendar/Gmail
    memory_service.py  Facts
    context_service.py Entity graph for the PA
    finance_service.py / health_service.py
    onboarding_service.py
    openai_service.py  Chat + tools + embeddings
    web_search_service.py Serper
    usage_service.py   7-day metrics
  models/              Pydantic domain/API types
  database/            Supabase client
  constants/           Asset types, goal modules, project links
migrations/            Ordered SQL (see GETTING-STARTED.md)
prompts/               PA system prompt
tests/                 Service-level tests
web/                   Next.js 15 PWA
scripts/               smoke, seed, deploy
```

FastAPI routers (prefixes): `/auth`, `/chat`, `/actions`, `/missions`, `/inbox`, `/home` `/dashboard` `/weekly-brief` `/daily-brief` `/priorities` `/timeline`, `/tasks`, `/projects`, `/assets`, `/goals`, `/finance`, `/health-data`, `/integrations`, `/documents`, `/decisions`, `/events`, `/calendar`, `/memory`, `/usage`. Plus `GET /health`.

Frontend client: `web/src/lib/api.ts` (default base `/api` so the Next rewrite works on phones).

---

## 14. How to add a feature (required order)

1. **Domain / service** — `app/models/` + `app/services/` (or Action Engine). No React.
2. **Tests** — `tests/` with fake Supabase helpers (`tests/conftest.py`).
3. **API** — FastAPI route, Pydantic in/out, handler only delegates.
4. **UI** — page under `web/src/app/(app)/`, talk through `api.ts`. Reuse cards/lists (`RecordListPage`, `CreateRecordForm`, `EditSheet`).
5. If the PA should act on it: add a tool in `pa_agent.py`, map it in `chat_actions.py` / `action_executor.py`, and mention it in the system prompt if needed.
6. If it is a new table: add an idempotent migration, RLS using `can_read_record` / `can_write_record`, and a `storage_service` visibility default.

**Do not** put SQL, OpenAI, or ranking logic in React.

---

## 15. Local development

Prereqs: Python 3.11+, Node 18+, `.env` from `.env.example`, Supabase project with **all migrations in date order**, Storage bucket `documents`.

```bash
cp .env.example .env
pip install -r requirements.txt
uvicorn app.api.main:app --reload --port 8000   # :8000/docs

cd web && npm install && npm run dev            # :3000
```

If the UI hangs: `cd web && npm run dev:clean`.

Optional: `scripts/seed_demo_data.py` after login (set `SEED_USER_ID` / `SEED_HOUSEHOLD_ID`). Tests: `python3 -m pytest tests/ -q`. Smoke: `scripts/smoke_test.sh`.

iPhone: FastAPI + Next locally, ngrok on **3000**, Add to Home Screen. Details: [`IPHONE-TEST.md`](IPHONE-TEST.md), [`GETTING-STARTED.md`](GETTING-STARTED.md), [`AI-OPPSKRIFT.md`](AI-OPPSKRIFT.md) (AI phases + Google).

---

## 16. Roadmap (vision vs now)

Historical vision versions in `PRODUCT-VISION.md` mixed Streamlit-era sequencing. Interpret the **intent**, not the old V1–V8 labels.

**Now (Mini-jarv daily driver)**

- Chat with proposal-mode tool calling
- Memory + onboarding seed
- Documents + embeddings
- Assets + tasks + inbox
- Projects, goals, decisions, timeline
- Hjem briefs + priority list
- Calendar + Google
- Manual finance + health
- Usage tracking for the 7-day test

**Next (only after daily use is real)**

1. Deploy (Fly + Vercel) if not already the daily URL
2. Tighten Priority Engine so Hjem is trustworthy
3. HouseOS beta: one home asset + docs + tasks + weekly brief
4. Document intelligence polish (versioned insurance, accept/keep both/ignore)
5. Timeline as an automatic year-in-review

**Later**

- Outlook / OneDrive / Microsoft To Do
- Apple Health, Garmin, Strava
- Banks, insurers, accounting
- Decisions with alternatives + expected vs actual outcome
- Self-evolve proposing modules from request patterns
- Capacitor store apps
- Voice client, same FastAPI
- LifeOS packaging (HouseOS + VehicleOS + …)

**Explicitly later / do not do now**

- Native rewrite
- Deep finance/health integrations
- Scaling marketing
- Treating Self-Evolve as a user-facing product

---

## 17. Analytics (product, not vanity)

Track: `app_opened`, dashboard/home viewed, task/asset created, question asked, document uploaded.

Goal: learn which features create **return visits**. Settings already surfaces 7-day opens / streak.

---

## 18. Working with this repo as Claude

- Prefer editing services + tests over adding UI chrome.
- Match existing Norwegian user-facing strings; keep code identifiers English.
- When fixing chat/AI: think tools + Action Engine + confirmation UX, not longer system prompts alone.
- When something feels missing in the UI, check whether the service already exists (`action_engine`, `brief_service`, `document_intelligence`).
- `ARCHITECTURE-vision.md` still describes a Streamlit→Next migration. That migration is **done**. Use `ARCHITECTURE.md` + this file for current topology.
- `PRODUCT-VISION.md` stack section still says “Frontend: Streamlit”. Treat as historical. Next.js is production UI.

---

## 19. Glossary

| Term | Meaning |
|------|---------|
| Mini-jarv | PWA brand / default assistant name |
| WilliamOS | Repo and platform name |
| HouseOS | First commercial wedge (home PA) |
| LifeOS | Long-term category |
| Hjem | Home screen (priorities + briefs) |
| Eiendeler | Assets |
| Oppgaver | Tasks |
| Minne | Durable PA memory |
| Historikk | Timeline of events |
| Action Engine | Only write path for domain mutations |
| Proposal mode | Chat tool calls wait for user confirm |
| Oppdrag / mission | Multi-step plan of proposed actions |
| User #0 | William — must be the daily driver before beta |
| Self-Evolve | Background motor that logs needs; not a product |

---

## 20. One paragraph to remember

William is building a **personal operating system** that starts as his own Chief of Staff (Mini-jarv / WilliamOS), ships first as a paid **house assistant** (HouseOS), and becomes **LifeOS** — the system of record for assets, documents, maintenance, money, health, goals, and decisions. The interface is a Norwegian mobile-first PWA. The intelligence is Python: a tool-calling agent that proposes structured actions, an Action Engine that executes them, and a growing life graph in Supabase. We are not building a chatbot. We are building the layer that answers “what should I do this week?” and then does it.
