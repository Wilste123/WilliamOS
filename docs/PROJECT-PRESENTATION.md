# WilliamOS — Project presentation for Claude

This is the single briefing document for humans and coding agents. It explains **what we are building, why, the long-term vision, and what the code does today**.

Shorter working contract: [`CLAUDE.md`](../CLAUDE.md) at repo root.

Canonical source docs (this file synthesizes them against the current codebase):

| Doc | Role |
|-----|------|
| [`PRODUCT-VISION.md`](PRODUCT-VISION.md) | LifeOS / HouseOS mission and moat |
| [`ENDGOAL.md`](ENDGOAL.md) | Full Personal Assistant platform spec |
| [`ARCHITECTURE-vision.md`](ARCHITECTURE-vision.md) | Target architecture |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Developer architecture reference |
| [`MVP-FOCUS.md`](../MVP-FOCUS.md) | Current daily-use Mini-jarv scope |
| [`HOUSEOS-BETA.md`](HOUSEOS-BETA.md) | First paying-user wedge |
| [`AI-OPPSKRIFT.md`](AI-OPPSKRIFT.md) | How the AI engine is used day to day |

---

## 1. Identity — names you will see

These names are **one product line**, not four apps.

| Name | What it means | Who sees it |
|------|----------------|-------------|
| **WilliamOS** | Internal platform / repo / API title. Personal Chief of Staff. | Developers, FastAPI (`title="WilliamOS API"`) |
| **Mini-jarv** | Current consumer brand of the PWA (icons, `<title>`, manifest). | End user on iPhone / desktop |
| **HouseOS** | First commercial product: "your house PA". Same backend, narrowed to home + docs + maintenance + tasks. | Beta users, go-to-market |
| **LifeOS** | Long-term vision: the operating system for everything people own, maintain, and decide about. | Strategy, not a ship target yet |
| **Self-Evolve** | Not a product. An internal engine that logs needs and suggests modules. Hidden route `/self-evolve`. | Founder / agents |

Evolution path (do not skip steps):

```
WilliamOS (internal daily driver)
    → HouseOS (beta, 99 kr/mnd, homeowners)
        → LifeOS (platform: House + Vehicle + Cabin + Finance + Family + …)
```

Founder: **William**, building in **Trondheim**, Norway. User #0 is William. Norwegian households are the design center.

---

## 2. One-sentence pitch

Mini-jarv is a personal Chief of Staff that captures life into structured objects (assets, tasks, documents, decisions) and tells you what to do this week — then **does the work** after you confirm.

---

## 3. The problem

People’s life-admin is scattered across:

- folders, email, banks, insurers
- spreadsheets, notes apps, calendars
- their own head

The feeling we exist to kill:

> "I feel like I am forgetting something."

Concrete HouseOS wedge (first commercial pain):

> Nobody has their home organized. Documents, maintenance, and insurance live nowhere.

---

## 4. Mission, vision, north star

### Mission

Help the user **Understand → Prioritize → Act → Learn**.

LifeOS (long term) is the place where people organize, understand, and make better decisions about everything they own.

### Vision (category positioning)

- Apple organizes devices.
- Microsoft organizes work.
- Google organizes information.
- **LifeOS organizes life.**

Long-term domains: bolig, hytte, bil, båt, økonomi, dokumenter, vedlikehold, prosjekter, familieverdier.

### North star

The user asks:

> **"Hva bør jeg gjøre denne uka?"**

and gets a **correct, ranked answer** grounded in their tasks, goals, projects, documents, assets, inbox, calendar, and (later) email.

The product feature behind this is the **Priority Engine** (`build_priority_engine` in `app/services/action_engine.py`). Home (`/home`) surfaces it as ukens brief + tappable priorities + executable daily proposals.

### Success metric

Days per week the user opens the app. Target: **5+**. Tracked in Settings as the 7-day test (opens, streak, unique days).

If William does not use Mini-jarv daily, **simplify — do not add modules**.

---

## 5. What we are NOT building

- Not a chatbot.
- Not a generic task manager.
- Not a dashboard for dashboards' sake.
- Not an ERP / CRM / Excel clone.
- Not "AI that only advises."

Bad: "Du burde opprette en oppgave."  
Good: yellow action card → **Oppgave opprettet** after confirm.

If a feature does not improve **overview, prioritization, or decisions**, it probably does not belong.

Design references: Apple, Linear, Arc, ChatGPT Mobile. Dark, cards, mobile-first, calm, minimal.

---

## 6. Product principles (memorize these)

### 1. AI executes. It does not only answer.

Tool-calling → Action Engine. Mutating tools require a confirmation card (`PROPOSE_TOOLS` in `app/services/chat_actions.py`). Safe tools (inbox capture, save_memory, complete_task) may run immediately.

### 2. Everything is structured data.

Inbox text becomes Asset / Task / Project / Document / Event / Decision — not another note blob.

### 3. The user should not think in folders.

Documents attach to assets and projects. Search is semantic. History is a timeline of events, auto-appended on mutations.

### 4. Asset-first.

Life is modeled around things the user owns or is considering:

```
Mazda CX-5
  ├── Oppgaver
  ├── Dokumenter
  ├── Historikk (events)
  ├── Kostnader (later / finance)
  └── Beslutninger
```

Asset types in code: `vehicle`, `boat`, `property`, `cabin`, `other` (`app/constants/asset_types.py`). UI labels: Bil, Båt, Bolig, Hytte, Annet.

Statuses: `active` | `considering_purchase` | `inactive`.

Example inbox capture:

> "Vurderer å kjøpe Pioner 320 til 25 000"

System suggests: Asset Pioner 320, value 25 000, status considering_purchase.

### 5. Inbox is the front door.

Everything enters through Inbox: typed capture, document signals, suggested updates. User Accept / Ignore.

### 6. Python is the brain. UI is disposable.

Next.js must never own business logic. Deleting `web/` must not require rewriting services.

### 7. Confirmation before mutation (chat)

Create/update/delete from the PA shows a **yellow action card**. `POST /actions/execute` (or batch) runs only after Utfør.

### 8. Data belongs to the user

Settings must support view / edit / export / delete of stored data. GDPR-aligned: Supabase **eu-north-1 (Stockholm)**.

---

## 7. Long-term product map (LifeOS)

```
LifeOS
├── HouseOS      ← first commercial wedge
├── VehicleOS
├── CabinOS
├── FinanceOS
├── FamilyOS
└── Future modules
```

Under the Personal Assistant (WilliamOS), planned modules:

| Module (NO) | Purpose | Code status (Aug 2026) |
|-------------|---------|------------------------|
| Hjem | Priorities, brief, net worth | Shipped (`/home`) |
| Chat | Natural interaction + tools | Shipped, streaming SSE |
| Inbox | Capture and triage | Shipped |
| Oppgaver | Tasks | Shipped |
| Eiendeler | Home / cabin / car / boat (former HouseOS) | Shipped + detail pages |
| Økonomi | Net worth, accounts | Thin module exists; **not the wedge** |
| Helse | Weight, activity, later Apple/Garmin/Strava | Thin module exists; **not the wedge** |
| Mål | Goals with next step + progress | Shipped |
| Prosjekter | Projects + entity links | Shipped |
| Dokumenter | Upload, classify, embed, ask | Shipped + embeddings |
| Beslutninger | Decision log | Shipped |
| Kalender | Internal + Google two-way | Shipped |
| Historikk / Timeline | Auto life history | Shipped via `events` |
| Minne | Durable facts for the PA | Shipped |
| Integrasjoner | Google Calendar / Gmail | Shipped |
| Analytics | Usage log for 7-day test | Shipped (`usage_log`) |
| Self-Evolve | Log needs → suggest modules | Dev-only |

ENDGOAL also lists Learning and Life Transitions — not built yet.

---

## 8. What ships today (Mini-jarv MVP)

Goal: a **small, excellent daily-use app**. Core loop:

1. Open app → **Hjem** (greeting, formue, ukens brief, "Forslag fra Mini-jarv")
2. **Chat** with the PA (stream, quick actions, persistent history)
3. Capture in **Inbox** → apply AI suggestions
4. Track **Oppgaver** and **Eiendeler**
5. Tune **Innstillinger** (assistant name, usage)

**Brand in UI:** Mini-jarv.  
**Nav:** mobile bottom bar (Hjem, Chat, Inbox, Oppgaver, Mer). Desktop sidebar has the full set.

**Definition of done** (from MVP-FOCUS — still the gate):

- Login on Mac and iPhone (ngrok / PWA)
- Hjem shows correct net worth + weekly brief
- Chat streams with quick actions
- Inbox capture + apply works
- Task CRUD + complete
- Asset CRUD + detail updates Hjem net worth
- Document upload
- Assistant name saves
- Used daily for 7 days without Streamlit

**After 7-day pass:** deploy, then HouseOS beta (3–5 friends/family, 99 kr/mnd, one home asset + docs + tasks). Do **not** build out Økonomi/Helse or App Store until User #0 is a daily driver and beta users open weekly without nagging.

---

## 9. User journeys the product must support

### Morning (2 min)

Open Hjem → read ukens brief → tap a priority or Utfør 1–3 proposals (overdue tasks, inbox suggestions, calendar prep).

### Capture during the day

Dump a thought in Inbox or chat (`fang i innboks …`). Do not use Apple Notes.

### Chat as Chief of Staff

Examples that must work:

- "Lag oppgave: ring rørlegger, frist fredag" → yellow card → Utfør → task exists
- "Mazda must pass reinspection before October 18" → understand the action, propose task linked to Mazda
- "Hva står om taket i hytteforsikringen?" → hybrid document search + citation chips
- `oppdrag: Forbered hyttetur neste helg` → multi-step plan, confirm each (or Utfør alle)
- "Hva bør jeg gjøre i morgen?"

### Document intelligence

Upload insurance PDF → classify type (insurance/invoice/contract/service/warranty) → suggest asset link (e.g. Mazda CX-5) → Accept / Keep both / Ignore.

### Asset detail

Open Eiendel → see linked tasks, documents, timeline events, value. This is the HouseOS heart.

---

## 10. Domain model (core objects)

Every mutation should leave a trail on **Timeline** (`events` table) via Action Engine `append_event`.

| Object | Table | Meaning |
|--------|-------|---------|
| **Asset** | `assets` | Thing you own or might buy. Center of gravity. |
| **Task** | `tasks` | Action with due date, priority 1–3, optional asset/project |
| **Project** | `projects` | Multi-step work; `next_action`; links to assets/goals/docs |
| **Goal** | `goals` | Outcome with progress 0–100, `next_step`, module (health/finance/asset/project/general) |
| **Document** | `documents` | File in Storage + extracted text + embedding |
| **Decision** | `decisions` | Open vs decided; reasoning belongs here long-term |
| **Event** | `events` | Auto history (asset_created, task_updated, …) |
| **Inbox item** | `inbox_items` | Raw capture + `suggestions[]` |
| **Memory** | `memory_items` | Durable PA facts |
| **Calendar event** | `calendar_events` | Internal calendar; may sync Google |
| **Finance account** | `finance_accounts` | Manual balances; net worth = accounts + asset values |
| **Health** | health tables | Manual metrics for now |
| **Chat history** | `chat_history` | Persistent PA threads |
| **Usage** | `usage_log` | app_opened and similar |
| **Requests log** | `requests_log` | Self-Evolve signals |
| **Household** | `households` + `household_members` | Family sharing |
| **Profile** | `user_profiles` | display_name, assistant_name, preferences, onboarding |

### Tenancy

```
user_id       UUID
household_id  UUID
visibility    TEXT  -- 'private' | 'household'   (ARCH doc also mentions 'shared'; DB check is private|household)
```

Inbox, memory, chat, requests_log default **private**. Assets/tasks/projects default **household**. RLS in Supabase is the access control; FastAPI passes the user JWT so policies apply server-side.

### Project links

`PROJECT_LINK_TYPES`: asset, goal, document, finance_account, task, decision.

---

## 11. AI architecture (the actual brain)

### PA agent

`app/agents/pa_agent.py` + `prompts/pa_system_prompt.txt`

- Default language: **Norwegian**
- Tone: direct, practical, concrete
- Models: daily `gpt-4o-mini` (`OPENAI_MODEL`), planner `gpt-4o` (`OPENAI_MODEL_PLANNER`), embeddings `text-embedding-3-small`
- Streaming: `POST /chat/stream` (SSE)
- Context: memory, document retrieval, entity graph (`context_service`), onboarding block, intent hint, recent chat

### Tools the model can call

Creates/updates (proposal): assets, tasks, projects, decisions, goals, documents, calendar events, apply_inbox_suggestion, deletes.

Immediate / read: list_*, get_priority_focus, get_weekly_brief, search_documents, web_search (Serper), capture_inbox, complete_task, save_memory, list_upcoming_schedule, sync_google_calendar.

**Rule in prompt:** if it should be a task, call `create_task` — do not only mention it in prose.

### Proposal pipeline

1. Model calls a mutating tool  
2. `chat_actions.build_proposal` → action card in the UI  
3. User taps Utfør  
4. `POST /actions/execute` → `action_executor.execute_chat_action` → Action Engine / calendar / inbox  

AI **suggests**. Action Engine **writes**.

### Missions

Chat prefix `oppdrag:` or `POST /missions/plan`. LLM planner with rule-based fallback (`mission_service.py`) for hytte, forsikring, møter, etc. Returns a list of proposals.

### Priority + briefs

- `build_priority_engine` — scores overdue tasks, due-soon, P1–P3, active projects, goals, inbox, considering_purchase assets  
- `build_weekly_brief` — "Hva bør jeg gjøre denne uka?"  
- `build_daily_brief` (`brief_service.py`) — executable proposals on Hjem from inbox / overdue / calendar  
- `build_home_summary` — greeting, net worth, metrics, focus_items  

### Document intelligence

- Classify by keywords (forsikring, faktura, kontrakt, service, garanti)
- Suggest asset by name overlap
- Embeddings on upload; `POST /documents/reindex-embeddings` for backfill
- Hybrid search in chat (`retrieval_service`)

### Intent router

Lightweight hints: schedule, documents, finance, mission, general.

### Self-Evolve

Logs chat requests; counts keywords (lån, bolig, bil, hytte, forsikring, …). Not user-facing.

---

## 12. Architecture (current = target for clients)

```
iPhone PWA / Desktop / (later Capacitor, later Voice)
              │
              ▼
     Next.js `web/`  (Tailwind, shadcn, dark, mobile-first)
              │  HTTPS + Bearer JWT
              │  Browser → /api/*  → Next rewrite → FastAPI
              ▼
     FastAPI `app/api/`  auth middleware, OpenAPI, SSE
              │
              ▼
     Services + Agents   Action Engine, PA, briefs, retrieval
              │
              ▼
     Domain `app/models/`  (no I/O)
              │
              ▼
     Supabase (eu-north-1) · OpenAI · Google · Serper
```

**Import direction is downward only.** Forbidden: frontend → OpenAI/Supabase data; services → React; Next.js API routes for app logic.

Auth: Supabase email auth on the client for session. Access token sent as `Authorization: Bearer`. Refresh tokens may round-trip via `X-Access-Token` / `X-Refresh-Token` headers.

Deploy target: Vercel (web) + Fly.io (API, `fly.toml`) + Supabase.

Mobile strategy: **PWA first** (Add to Home Screen). Capacitor later, same UI, no native rewrite. Do not start a second frontend.

Streamlit is dead for production. Do not revive it.

---

## 13. Repository map

```
WilliamOS-afui/
├── CLAUDE.md                 ← agent working contract
├── docs/PROJECT-PRESENTATION.md  ← this file
├── app/
│   ├── api/                  FastAPI: main.py, middleware, routes/*
│   ├── agents/               pa_agent, intent_router, self_evolve
│   ├── services/             action_engine, action_executor, chat_actions,
│   │                         brief, mission, retrieval, embeddings,
│   │                         calendar, google, documents, finance, health, …
│   ├── models/               Pydantic domain
│   ├── constants/            asset_types, goal_modules, project_links
│   └── database/             supabase wrappers
├── web/src/
│   ├── app/(app)/            authenticated pages (home, chat, inbox, …)
│   ├── components/           AppShell, BottomNav, cards, forms
│   └── lib/api.ts            only HTTP client to FastAPI
├── migrations/               ordered SQL for Supabase
├── prompts/pa_system_prompt.txt
├── tests/                    pytest, fake supabase in conftest
└── scripts/                  smoke_test, seed_demo_data, start-dev
```

How to add a feature: **models → services/tests → FastAPI → web**. See `docs/ARCHITECTURE.md`.

---

## 14. Frontend surface (routes)

| Route | Module |
|-------|--------|
| `/home` | Hjem (legacy `/dashboard` redirects here) |
| `/chat` | PA |
| `/inbox` | Capture |
| `/tasks` | Oppgaver |
| `/assets`, `/assets/[id]` | Eiendeler + detail |
| `/projects`, `/projects/[id]` | Prosjekter |
| `/goals`, `/goals/[id]` | Mål |
| `/decisions` | Beslutninger |
| `/documents` | Dokumenter |
| `/calendar` | Kalender |
| `/timeline` | Historikk (`/events` redirects here) |
| `/finance` | Økonomi (thin) |
| `/health` | Helse (thin) |
| `/integrations` (+ `/callback`) | Google OAuth |
| `/memory` | Minne |
| `/settings` | Profile, export, 7-day stats |
| `/onboarding` | First-run: assistant name, primary use, assets, focus |
| `/login` | Auth |
| `/self-evolve` | Hidden |

UI language: **Norwegian** (`<html lang="no">`). Assistant display name is user-configurable (default Mini-jarv / WilliamOS naming in prompts).

---

## 15. FastAPI surface (mental map)

Routers mounted in `app/api/main.py`:

`/auth`, `/chat`, `/actions`, `/missions`, `/inbox`, `/home`, `/dashboard`, `/weekly-brief`, `/daily-brief`, `/priorities`, `/timeline`, `/tasks`, `/projects`, `/assets`, `/goals`, `/health-data`, `/finance`, `/integrations`, `/documents`, `/decisions`, `/events`, `/calendar`, `/memory`, `/usage`, `/health` (liveness).

OpenAPI: `http://localhost:8000/docs`.

---

## 16. Integrations (now vs later)

**Now**

- OpenAI tool-calling + embeddings
- Supabase Auth / Postgres / Storage / RLS / pgvector
- Google Calendar + Gmail OAuth (`docs/GOOGLE-SETUP.md`) — two-way calendar; reconnect if scopes were read-only
- Serper web search in chat

**Planned (do not build until core loop is daily)**

- Microsoft: Outlook, Calendar, OneDrive, To Do
- Health: Apple Health, Garmin, Strava
- Banks, insurers, accounting, credit reporting

---

## 17. Monetization (HouseOS / LifeOS)

From product vision — not implemented in code yet:

| Plan | Price |
|------|-------|
| Person | 99 kr/mnd |
| Familie | 199 kr/mnd |
| Premium | 299 kr/mnd |

Beta: charge **99 kr/mnd** via Vipps/faktura. No App Store until retention is real.

---

## 18. Moat

Not the chat UI. **Structured life history:**

- assets with timelines
- documents linked to home/car/boat
- decisions with context
- auto-generated events on every action

Every week of use makes switching harder. Protect this data model. Do not dump life into unstructured chat logs.

---

## 19. Roadmap vs reality

Vision doc V1–V8 is historical. **Reality in Aug 2026:** Chat, memory, documents, assets, tasks, projects, dashboard/Hjem, tool calling, Action Engine, timeline, decisions, Self-Evolve (internal), calendar, missions, embeddings, onboarding, Google — already exist as a prototype daily driver.

What is **not** done:

- HouseOS launch as a focused commercial skin
- LifeOS multi-product
- Deep Økonomi / Helse / email ingestion
- Capacitor store apps
- Generated TypeScript client from OpenAPI
- True "what should I do" quality at Chief-of-Staff level (Priority Engine is heuristic, not a learned planner)
- Decision objects storing alternatives + expected vs actual outcome in full
- Bank/insurance integrations

**Near-term sequence (product, not calendar estimates):**

1. William uses Mini-jarv 5+ days/week (7-day test, then 30 days)
2. Production deploy (Vercel + Fly + Supabase) if not already the daily host
3. HouseOS beta: 3–5 homeowners, one house asset, 99 kr/mnd
4. Only then: deepen document intelligence, email signals, native wrapper

---

## 20. Language and voice

| Surface | Language |
|---------|----------|
| UI strings, PA replies, action card labels | Norwegian |
| Code identifiers, comments, commit messages, most architecture docs | English |
| User-facing product nouns | Hjem, Inbox, Oppgaver, Eiendeler, Minne, … |

PA first-hello may mention: data in Supabase eu-north-1, GDPR, founder William in Trondheim.

---

## 21. How Claude should behave in this repo

1. Read this file + `CLAUDE.md` before large changes.
2. Keep the Chief of Staff loop sharp: Hjem brief, Chat proposals, Inbox, Tasks, Assets.
3. Put new intelligence in Python services, not in React.
4. Mutating PA tools must stay behind confirmation unless they are explicitly in the immediate-exec set.
5. Do not expand Økonomi/Helse/marketing/App Store to postpone daily-use quality.
6. Do not bypass RLS or write user data without `user_id` / visibility.
7. Prefer one simplified flow over a new module.
8. After behavior changes, add or update pytest coverage under `tests/`.
9. UI copy stays Norwegian; do not mix English buttons into the PWA without a product reason.

---

## 22. Local run (agent cheat sheet)

```bash
cp .env.example .env          # OpenAI + Supabase (+ optional Google, Serper)
pip install -r requirements.txt
uvicorn app.api.main:app --reload --port 8000

cd web && npm install && npm run dev   # http://localhost:3000
```

Migrations: run SQL in `migrations/` in date order (see `docs/GETTING-STARTED.md`). Storage bucket `documents`. Tests: `python3 -m pytest tests/ -q`. iPhone: ngrok + PWA (`docs/IPHONE-TEST.md`).

---

## 23. Final rule

We are not building a chatbot.

We are building a **personal operating system** — starting as William’s Chief of Staff, shipping first as a house PA, aiming to become LifeOS.

When in doubt: make the structured object, propose the action, wait for confirm, write through the Action Engine, append the timeline event.
