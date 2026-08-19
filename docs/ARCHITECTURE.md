# WilliamOS — Architecture

This document is the **developer reference** for WilliamOS architecture: current state, target state, layer rules, and how to add features without coupling to UI technology.

For product direction and long-term vision, see [`docs/ARCHITECTURE-vision.md`](ARCHITECTURE-vision.md).

---

## Current State

WilliamOS is in **prototype phase**. The architecture is intentionally moving toward a stable target; today’s code reflects partial progress.

| Component | Status |
|-----------|--------|
| `app/services/`, `app/agents/` | Primary home of business logic — UI-agnostic |
| `app/models/` | Domain and data types |
| `app/database/` | Supabase wrappers; schema in `migrations/` |
| `app/api/` | FastAPI — **primary API** for Next.js (auth, CRUD, chat SSE, usage) |
| `web/` | Next.js PWA — production UI via FastAPI |

**Notes:**

- Next.js is the only client UI — all traffic goes through FastAPI

---

## Target State

```
┌─────────────────────────────────────────────────────────┐
│  Clients: Web · PWA · iPhone · Android · Voice (future) │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│  Next.js + React + Tailwind + shadcn/ui  (`web/`)        │
│  Mobile-first · PWA · Capacitor wrapper later            │
└──────────────────────────┬──────────────────────────────┘
                           │  HTTPS + Bearer JWT
┌──────────────────────────▼──────────────────────────────┐
│  FastAPI  (`app/api/`)  — single public API              │
│  Auth middleware · OpenAPI · SSE chat                    │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│  Application layer  (`app/services/`, `app/agents/`)     │
│  Action Engine · orchestration · agent suggestions       │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│  Domain layer  (`app/models/`)                         │
│  Pure types and business rules — no I/O                  │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│  Infrastructure  (`app/database/`, OpenAI, integrations)│
└─────────────────────────────────────────────────────────┘
```

**Target rules:**

- All production clients call **FastAPI only** for application data and AI
- Frontend never calls OpenAI or Supabase directly
- Python backend contains all business logic, agent logic, and integrations

---

## Layer Responsibilities

### Next.js frontend (`web/`)

| Responsibility | Detail |
|----------------|--------|
| Display | Render modules (Inbox, Chat, Dashboard, Assets, …) |
| Input | Forms, chat, file pickers |
| API calls | Fetch/mutate via FastAPI with JWT |
| Not allowed | Business logic, OpenAI, Supabase data/storage, domain validation |

**Stack:** Next.js, React, Tailwind, PWA first, Capacitor later.

### API layer (`app/api/`)

| Responsibility | Detail |
|----------------|--------|
| Public interface | All production clients enter here |
| Auth | Validate Supabase JWT → `UserContext` |
| Contract | Pydantic request/response models, OpenAPI at `/docs` |
| Delegation | Handlers call services — no business logic in routes |

Example routes (target surface grows over time):

```
GET  /dashboard          GET  /inbox
GET  /assets             POST /tasks
POST /chat               POST /chat/stream
GET  /documents          POST /documents/upload
```

**Rule:** No Next.js API routes for application logic. FastAPI is the backend.

### Application layer (`app/services/`, `app/agents/`)

Orchestration and use cases. UI-agnostic — callable from FastAPI, CLI, or workers.

| Area | Examples |
|------|----------|
| Action Engine | `create_task`, `apply_inbox_suggestion`, all mutations |
| Agents | `pa_agent`, document intelligence, self-evolve |
| Services | storage, memory, retrieval, auth context, profile |

**Rules:**

- May import `app/models` and infrastructure (`app/database/`, OpenAI wrappers)
- Must **not** import any frontend code
- AI suggests; Action Engine executes

### Domain layer (`app/models/`)

Pure Python types — User, Asset, Task, Project, Decision, Event, Document, …

**Rules:** No I/O, no FastAPI, no OpenAI, no Supabase.

### Infrastructure layer (`app/database/`, OpenAI, future integrations)

Thin wrappers around external systems. Provider changes affect only this layer.

---

## Import Rules

```
Allowed:
  web/ (Next.js)         →  FastAPI (HTTP)
  app/api/               →  app/services, app/agents, app/models
  app/services/          →  app/models, app/database, infrastructure
  app/agents/            →  app/services, app/models
  app/database/          →  external SDKs (Supabase, OpenAI)

Not allowed:
  app/models/            →  any upper layer
  app/services/          →  web/
  web/                   →  app/database/
  web/                   →  OpenAI directly
  web/                   →  Supabase data/storage directly
```

Imports flow **downward only**. If a lower layer needs something from above, extract shared code into `app/models/` or a new service.

---

## Why Next.js for Production UI

| Concern | Benefit |
|---------|---------|
| Mobile UX | Mobile-first, PWA, touch-native patterns |
| Design quality | Tailwind — premium, consistent styling |
| Product scale | Component architecture for many modules |
| Multi-client | Same React UI → PWA → Capacitor |
| Separation | Clear UI/API boundary via FastAPI |

**Alternative:** Vite + React SPA can work for UI-only clients, but WilliamOS standardizes on **Next.js** for routing, layouts, and the PWA → Capacitor roadmap.

---

## Why Capacitor Is Later

Capacitor does not replace React or Next.js. It wraps the **same** web UI as a native shell for App Store / Play Store.

```
Phase A: Next.js in browser + PWA install
Phase B: Capacitor wraps identical build → iOS / Android
```

Build Capacitor only when PWA traction justifies store distribution. Do not maintain a separate native UI codebase.

---

## Migration Plan (completed phases)

| Phase | Status |
|-------|--------|
| **1. FastAPI surface** | Done — auth middleware, OpenAPI, CRUD, chat SSE |
| **2. Next.js frontend** | Done — all modules in production nav |
| **3. PWA** | Done — manifest, mobile navigation |
| **4. Capacitor** | Future — wrap Next.js for store apps if traction exists |

Services, domain, and infrastructure remain stable across all phases.

---

## How to Add a New Feature

Follow this order to avoid UI coupling:

1. **Domain / logic** — add types in `app/models/` and functions in `app/services/` (or Action Engine). No React.

2. **Tests** — exercise the service in `tests/` using fake Supabase helpers.

3. **API** — add FastAPI route with Pydantic models. Handler delegates to service.

4. **UI** — Next.js feature module in `web/` calling the API.

5. **Never** put business logic, OpenAI calls, or Supabase queries in frontend code.

---

## Data Model Notes

All user data is scoped with:

```sql
user_id       UUID NOT NULL
household_id  UUID
visibility    TEXT  -- 'private' | 'shared'
```

RLS in Supabase enforces access. FastAPI uses the user's JWT so the same policies apply server-side.

---

## Deployment (Target)

| Component | Service |
|-----------|---------|
| `web/` (Next.js) | Vercel or Cloudflare Pages |
| `app/api/` (FastAPI) | Fly.io or Railway (EU region) |
| Database / Auth / Storage | Supabase (eu-north-1) |

---

## Quick Reference

| Question | Answer |
|----------|--------|
| Production frontend? | **Next.js** + React + Tailwind |
| API layer? | **FastAPI** for all clients |
| Where is the brain? | **Python** — services, agents, Action Engine |
| Mobile apps? | PWA first, **Capacitor** wrapper later |
| Can frontend call Supabase? | **No** (auth session only; all data via FastAPI) |
| Can frontend call OpenAI? | **No** |
