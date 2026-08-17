# WilliamOS Architecture Vision

This document describes the **target architecture** for WilliamOS — where the platform is going, not a comparison with today's implementation.

**Core principle:** UI is disposable. The Python backend is the brain.

---

## 1. Product Direction

WilliamOS is being built as a personal AI assistant — a **personal Chief of Staff**.

It is not a chatbot. It helps users understand their life, manage assets and goals, track projects and decisions, prioritize actions, and make progress visible over time.

**HouseOS** is not the whole product. It is a module/category under **Hjem** (Home).

**Planned modules under the Personal Assistant:**

| Module | Purpose |
|--------|---------|
| Hjem | Properties, cabins, vehicles, boats, home documents (former HouseOS) |
| Økonomi | Finance |
| Helse | Health |
| Mål | Goals |
| Prosjekter | Projects |
| Dokumenter | Documents |
| Beslutninger | Decisions |
| Læring | Learning |
| Inbox | Capture and triage |
| Timeline | Activity history |
| Analytics | Usage and value signals |

All modules share the same backend, domain model, and API. The UI presents them as parts of one platform.

**Long-term clients — one backend, many interfaces:**

```
WilliamOS
│
├── Web (Next.js PWA)
├── iPhone (Capacitor wrapper)
├── Android (Capacitor wrapper)
├── Desktop / PWA install
└── Voice Assistant (future)
```

---

## 2. Current State

Today WilliamOS is in **prototype phase**. This is acknowledged explicitly — it is not the target architecture.

| Area | Today |
|------|-------|
| UI | Streamlit (`frontend/`) used as temporary MVP interface |
| Business logic | Mostly in `app/services/` and `app/agents/` — correct direction |
| API | FastAPI exists (`app/api/`) but is **not yet** the sole entry point for all clients |
| Streamlit access | Calls `app/services` directly, bypassing FastAPI |
| Auth | Supabase auth integrated; household + visibility model in place |
| Frontend quality | Desktop-oriented, not production-grade mobile experience |

**What works well today:**

- Service layer is largely UI-agnostic (no Streamlit in services/agents)
- Action Engine pattern for data mutations
- Supabase as single storage layer with RLS
- Tests against service functions

**What is transitional, not target:**

- Streamlit as primary user interface
- Direct service calls from UI instead of API calls
- Partial FastAPI surface (chat, tasks, assets, etc. — not complete)

---

## 3. Target Architecture

All future clients follow the same path. No client talks to OpenAI or Supabase for application data.

```
iPhone / PWA / Web / Voice / Desktop
              │
              ▼
    Next.js / React frontend
    (Tailwind + shadcn/ui)
              │
              ▼
         FastAPI backend
    (auth, OpenAPI, SSE chat)
              │
              ▼
    Application services
    (orchestration, use cases)
              │
              ▼
       Core / domain logic
    (models, rules, Action Engine)
              │
              ▼
  Infrastructure integrations
              │
              ▼
Supabase · OpenAI · Email · Calendar · Future APIs
```

**Repository target layout:**

```
WilliamOS-afui/
├── app/                    # Python backend — the brain
│   ├── api/                # FastAPI — single public API
│   ├── services/           # Application / orchestration
│   ├── agents/             # AI agents (suggest, never mutate directly)
│   ├── models/             # Domain + Pydantic API types
│   └── database/           # Supabase / external I/O
├── web/                    # Next.js production frontend (target)
├── frontend/               # Streamlit prototype (temporary — delete later)
├── migrations/
└── tests/
```

---

## 4. Frontend Strategy

**Recommended production frontend:**

- **Next.js**
- **React**
- **Tailwind CSS**
- **shadcn/ui**
- **Mobile-first design**
- **PWA first** — installable on iPhone/Android via Add to Home Screen
- **Capacitor later** — App Store / Play Store packaging when product traction exists

**Why Next.js (not Streamlit) for production UI:**

- Premium, responsive web experience on Mac, PC, tablet, and phone
- Component model suited to complex, module-based product UI
- Strong ecosystem for auth flows, routing, layouts, and PWA
- Same codebase scales from browser to installed app

**Why Capacitor is a later step, not a separate app:**

- Capacitor wraps the **same** Next.js/React UI — it is packaging, not a rewrite
- Goal is **one frontend codebase**, not separate web and native apps
- PWA covers most mobile needs before App Store submission is worth the cost

**Alternative (not recommended):** Vite + React SPA can achieve similar UI goals, but **Next.js is the chosen direction** for WilliamOS because of layout/routing conventions, production readiness, and alignment with the long-term PWA → Capacitor path.

**Next.js rule:** Next.js is a **frontend only**. It must not duplicate backend logic via Next.js API routes. All application data and AI flows go through FastAPI.

---

## 5. Backend Strategy

**Python / FastAPI is the brain.**

Everything that makes WilliamOS intelligent and trustworthy lives in the backend:

| Responsibility | Location |
|----------------|----------|
| Agent orchestration | `app/agents/` |
| Action Engine (all mutations) | `app/services/action_engine.py` |
| Prioritization engine | `app/services/` |
| Document intelligence | `app/services/document_service.py`, retrieval |
| Email / calendar signal processing | Infrastructure + services (future) |
| User snapshot / data preview | `app/services/` |
| Analytics | Service layer → Supabase |
| Integrations | Infrastructure layer |
| Domain logic and validation | `app/models/` + services |

**Frontend responsibilities:** display data, collect input, call FastAPI. Nothing else.

**AI rule:** AI suggests actions. The Action Engine executes after user confirmation. AI never writes directly to storage.

---

## 6. Layer Rules

Imports flow **downward only**.

```
Allowed:
  frontend (Streamlit)  →  services          [current prototype only]
  Next.js frontend      →  FastAPI (API)
  FastAPI (API)         →  services
  services              →  core / models
  services              →  infrastructure
  infrastructure        →  external APIs (Supabase, OpenAI, …)

Not allowed:
  core / models         →  frontend
  core / models         →  infrastructure
  services              →  Streamlit
  services              →  React / Next.js
  frontend (any)        →  Supabase directly
  frontend (any)        →  OpenAI directly
  Next.js               →  Next.js API routes for app logic  [use FastAPI instead]
```

**Auth note (target):** Login/signup may use Supabase Auth from the Next.js client for session management. The access token is sent to FastAPI as `Authorization: Bearer <token>`. All CRUD, storage, and AI operations go through FastAPI — never direct Postgres or Storage queries from the browser.

---

## 7. Streamlit Rule

Streamlit is a **prototype / lab interface**, not the long-term product UI.

**Streamlit may temporarily:**

- Render UI and collect user input
- Call service functions in `app/services/` and `app/agents/`

**Streamlit must not:**

- Contain business logic
- Contain domain validation
- Call OpenAI directly
- Call Supabase directly
- Depend on internal database schema details (use services as the boundary)

**End state:** Streamlit is removed or reduced to internal lab/admin tooling. Deleting `frontend/` must not require rewriting services, domain, or infrastructure.

---

## 8. Known Gaps

Explicit gaps between current state and target architecture:

| Gap | Current | Target |
|-----|---------|--------|
| API boundary | Streamlit → services directly | All clients → FastAPI → services |
| API completeness | Partial routes in `app/api/` | Full surface mirroring service operations |
| Auth middleware | Streamlit session state | JWT validation on every FastAPI route |
| Production UI | Streamlit | Next.js PWA |
| API contract | Informal | OpenAPI + generated TypeScript client |
| Mobile | Desktop Streamlit layout | Mobile-first Next.js + PWA |
| Native apps | None | Capacitor wrapper (later) |

These gaps are expected during prototype phase. Closing them is the migration project — not a platform rewrite.

---

## 9. Migration Plan

**Phase 1 — Thin Streamlit**

Refactor Streamlit so UI calls services only. No business logic, no direct OpenAI/Supabase in `frontend/`.

**Phase 2 — FastAPI surface**

Expose key service functions through FastAPI endpoints. Add auth middleware, Pydantic models, OpenAPI schema.

**Phase 3 — Next.js frontend**

Build `web/` (Next.js + React + Tailwind + shadcn/ui) against FastAPI. Start with auth, chat, inbox, dashboard.

**Phase 4 — Streamlit to lab**

Move Streamlit to internal lab/admin use only, or stop active development on it.

**Phase 5 — PWA**

Make the Next.js app installable (manifest, service worker, mobile-first navigation).

**Phase 6 — Capacitor (if traction)**

Wrap the same Next.js app with Capacitor for iPhone/Android store distribution. Single codebase, no separate native UI rewrite.

**Throughout all phases:**

- Services remain unchanged where possible
- Domain models remain unchanged
- Infrastructure remains unchanged
- Only UI layer and API surface expand

---

## 10. Acceptance Criteria

This vision document is satisfied when:

- [x] Next.js is stated as the recommended future production frontend
- [x] Streamlit is described as prototype/lab, not final product
- [x] Capacitor is described as mobile wrapper after Next.js is mature
- [x] FastAPI is described as the stable API layer for all clients
- [x] Python backend is described as the brain
- [x] Frontend must not call OpenAI or Supabase directly for application data
- [x] Current state, target architecture, known gaps, and migration plan are clearly separated
- [x] Vite + React is not presented as the primary target (only as an alternative)

For implementation details, layer responsibilities, and developer workflow, see [`docs/ARCHITECTURE.md`](ARCHITECTURE.md).
