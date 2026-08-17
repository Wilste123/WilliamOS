# Mini-jarv (WilliamOS)

Personal Chief of Staff — a daily-use app for tasks, assets, inbox capture, and AI chat.

**WilliamOS** → **HouseOS** → **LifeOS**. See [docs/PRODUCT-VISION.md](docs/PRODUCT-VISION.md).

---

## Stack

| Layer | Tech | Path |
|-------|------|------|
| Production UI | Next.js 15, React, Tailwind | `web/` |
| API | FastAPI | `app/api/` |
| Brain | Python services + PA agent | `app/services/`, `app/agents/` |
| Data | Supabase (Postgres, Auth, Storage) | `migrations/` |
| AI | OpenAI tool-calling | `app/agents/pa_agent.py` |
| Lab UI | Streamlit (dev only) | `frontend/` |

---

## Quick start

```bash
cp .env.example .env          # add OpenAI + Supabase keys
pip install -r requirements.txt
uvicorn app.api.main:app --reload --port 8000   # terminal 1

cd web && npm install && npm run dev             # terminal 2
```

Open http://localhost:3000 — create account, land on **Hjem**.

Full setup: **[docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)**

---

## MVP scope (Mini-jarv)

Daily-use modules: **Hjem · Chat · Inbox · Oppgaver · Eiendeler · Minne · Innstillinger**

Details: [MVP-FOCUS.md](MVP-FOCUS.md)

**Rule:** Use it daily for 7 days without Streamlit. If you don't use it, simplify — don't add features.

---

## Docs

| Doc | Purpose |
|-----|---------|
| [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) | Setup, migrations, run locally |
| [MVP-FOCUS.md](MVP-FOCUS.md) | Current MVP scope and definition of done |
| [docs/SEVEN-DAY-TEST.md](docs/SEVEN-DAY-TEST.md) | Daily-use validation gate |
| [docs/IPHONE-TEST.md](docs/IPHONE-TEST.md) | ngrok + PWA on iPhone |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Fly.io + Vercel deploy |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Developer reference |
| [docs/ARCHITECTURE-vision.md](docs/ARCHITECTURE-vision.md) | Target architecture |
| [docs/PRODUCT-VISION.md](docs/PRODUCT-VISION.md) | LifeOS / HouseOS vision |
| [docs/ENDGOAL.md](docs/ENDGOAL.md) | Target state spec (full platform) |

---

## Architecture rule

```
web/ → FastAPI → app/services/ → Supabase / OpenAI
```

Frontend never calls Supabase or OpenAI directly. All business logic lives in Python services.

---

## Scripts

```bash
scripts/smoke_test.sh      # pytest + health checks
scripts/seed_demo_data.py  # demo assets/tasks/inbox
scripts/start-dev.sh       # dev server instructions
```
