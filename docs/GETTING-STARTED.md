# WilliamOS — Getting Started

Mini-jarv (WilliamOS) runs as **FastAPI backend + Next.js PWA**.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- `.env` in repo root (copy from `.env.example`)
- Supabase project with migrations applied
- [ngrok](https://ngrok.com/) for iPhone testing (optional)

---

## 1. Supabase migrations

Run in Supabase SQL Editor, **in order**:

1. `migrations/2026-08-13_unified_storage.sql`
2. `migrations/2026-08-16_auth_households.sql`
3. `migrations/2026-08-16_assistant_name.sql`
4. `migrations/2026-08-17_usage_log.sql`
5. `migrations/2026-08-17_goals.sql`
6. `migrations/2026-08-17_finance_health_integrations.sql`
7. `migrations/2026-08-17_data_isolation_hardening.sql`
8. `migrations/2026-08-17_quarantine_orphan_records.sql`
9. `migrations/2026-08-18_google_integration.sql`
10. `migrations/2026-08-19_user_integrations_rls_fix.sql`
11. `migrations/2026-08-19_goals_projects_linking.sql`
12. `migrations/2026-08-19_memory_preferences.sql`
13. `migrations/2026-08-20_calendar_events.sql`

Create a Storage bucket named `documents` (or match `DOCUMENTS_BUCKET` in `.env`).

For Google Calendar/Gmail sync, see [docs/GOOGLE-SETUP.md](GOOGLE-SETUP.md).

---

## 2. Environment

**Backend** (`.env` in repo root):

```bash
OPENAI_API_KEY=...
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
DOCUMENTS_BUCKET=documents
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Frontend** (`web/.env.local` — optional):

```bash
API_PROXY_URL=http://127.0.0.1:8000
```

Do **not** set `NEXT_PUBLIC_API_URL=http://localhost:8000` for iPhone testing.

---

## 3. Install

```bash
pip install -r requirements.txt
cd web && npm install && cd ..
```

---

## 4. Run locally

**Terminal 1 — API:**

```bash
uvicorn app.api.main:app --reload --port 8000
```

Verify: http://localhost:8000/health

**Terminal 2 — Next.js:**

```bash
cd web
npm run dev
```

Open: http://localhost:3000

If the app hangs or shows module errors, use a clean dev start:

```bash
cd web && npm run dev:clean
```

---

## 5. iPhone via ngrok

1. Start FastAPI + Next.js as above
2. Do not set `NEXT_PUBLIC_API_URL` in `web/.env.local`
3. Run: `ngrok http 3000`
4. Open the ngrok HTTPS URL on iPhone
5. Add to Home Screen for PWA use

See [IPHONE-TEST.md](./IPHONE-TEST.md) for the full checklist.

---

## 6. Seed demo data (optional)

After first login, copy your user/household IDs to `.env`:

```bash
SEED_USER_ID=...
SEED_HOUSEHOLD_ID=...
python3 scripts/seed_demo_data.py
```

---

## Quick reference

| What | URL / command |
|------|----------------|
| Production UI | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Smoke test | `scripts/smoke_test.sh` |
| MVP scope | [MVP-FOCUS.md](../MVP-FOCUS.md) |
| 7-day test | [SEVEN-DAY-TEST.md](./SEVEN-DAY-TEST.md) |
| Deploy | [DEPLOY.md](./DEPLOY.md) |
| Architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Stuck on "Laster…" | Run `npm run dev:clean` in `web/`; hard-refresh browser |
| 401 on API calls | Log in again; check tokens in localStorage |
| CORS errors | Add your URL to `CORS_ORIGINS` in `.env` |
| Chat fails | Check `OPENAI_API_KEY` and FastAPI on :8000 |
| `assistant_name` column missing | Run assistant_name migration |
| Backend unreachable on phone | Use ngrok on port 3000 only — not localhost:8000 |
