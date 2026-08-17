# WilliamOS — Startup Instructions

Quick guide to run WilliamOS locally and test on iPhone via ngrok.

---

## Prerequisites

- Python 3.11+ with dependencies installed
- Node.js 18+ and npm
- `.env` configured in repo root (copy from `.env.example`)
- Supabase migrations run (see `Nextstep.md` section 1)
- [ngrok](https://ngrok.com/) installed (`brew install ngrok` on Mac)

**Required in `.env` (repo root):**

```bash
OPENAI_API_KEY=...
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
DOCUMENTS_BUCKET=documents
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Optional `web/.env.local`:**

```bash
# Leave NEXT_PUBLIC_API_URL unset — app uses /api proxy (recommended)
API_PROXY_URL=http://127.0.0.1:8000
```

Do **not** set `NEXT_PUBLIC_API_URL=http://localhost:8000` if you test on iPhone — that breaks on mobile.

---

## First-time setup

```bash
# From repo root
pip install -r requirements.txt

cd web
npm install
cp .env.local.example .env.local   # optional
cd ..
```

---

## Start the app (Mac / browser)

Open **three terminals** from the repo root:

### Terminal 1 — FastAPI backend (port 8000)

```bash
uvicorn app.api.main:app --reload --port 8000
```

Verify: http://localhost:8000/health → `{"status":"ok"}`

### Terminal 2 — Next.js frontend (port 3000)

```bash
cd web
npm run dev
```

Open: http://localhost:3000

Log in or create an account. After login you land on **Hjem** (home screen).

### Terminal 3 — Streamlit prototype (optional, port 8501)

```bash
streamlit run frontend/streamlit_app.py
```

Open: http://localhost:8501 — lab/MVP interface only; production UI is in `web/`.

---

## Start ngrok (test on iPhone)

On iPhone, `localhost` means the phone — not your Mac. Use **one ngrok tunnel on Next.js**; API calls go through Next.js proxy (`/api` → FastAPI on Mac).

### Steps

1. Start **Terminal 1** (FastAPI) and **Terminal 2** (Next.js) as above.
2. Remove `NEXT_PUBLIC_API_URL=http://localhost:8000` from `web/.env.local` if present.
3. Restart Next.js after any `.env.local` change.
4. In a **third terminal**:

```bash
ngrok http 3000
```

5. Copy the **Forwarding** HTTPS URL (e.g. `https://abc123.ngrok-free.app`).
6. Open that URL in Safari on your iPhone.
7. Log in as usual.

Next.js on your Mac receives `/api/*` requests from the phone and forwards them to `http://127.0.0.1:8000`.

### ngrok troubleshooting

| Problem | Fix |
|---------|-----|
| «Kunne ikke nå backend» | Ensure FastAPI is running on port 8000 |
| Still shows `localhost:8000` in error | Remove `NEXT_PUBLIC_API_URL` from `web/.env.local`, restart `npm run dev` |
| ngrok warning page | Tap through or add ngrok authtoken |
| Login works on Mac but not phone | Use ngrok URL only; do not use `localhost` on phone |

### Alternative: two ngrok tunnels

Only if you need a separate public API URL:

```bash
ngrok http 3000   # frontend
ngrok http 8000   # backend
```

Set in `web/.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://YOUR-API-URL.ngrok-free.app
```

Add your frontend ngrok URL to `CORS_ORIGINS` in `.env`.

---

## Where does «Nettoformue» come from?

The **Hjem** (home) screen shows **Nettoformue** from your **assets** in Supabase — not from a separate finance module yet.

### Data flow

```
Supabase `assets` table
  → field `estimated_value` on each asset
  → summed in Python
  → shown on home screen
```

### Code path

1. **Frontend** — `web/src/app/(app)/home/page.tsx` calls `fetchHome()` and displays `net_worth_formatted`.
2. **API** — `GET /home` in `app/api/routes/overview.py` → `build_home_summary()`.
3. **Logic** — `app/services/action_engine.py`:

```python
assets = list_records("assets")
net_worth_nok = sum(float(asset.get("estimated_value") or 0) for asset in assets)
```

4. **Formatting** — `format_net_worth_nok()` turns the sum into text like `6,2 MNOK`.

### How to change the number

Add or edit **Eiendeler** (assets) with **Estimert verdi** (`estimated_value`):

- In **Next.js**: Meny → Eiendeler (read-only list today)
- In **Streamlit**: Eiendeler → create/edit asset → «Estimert verdi»
- In **Supabase**: `assets.estimated_value` column

If no assets have `estimated_value`, home shows **—**.

**Note:** This is a simple sum of asset estimates — not full net worth (no debts, cash accounts, or investments unless stored as assets).

---

## Quick reference

| What | URL / command |
|------|----------------|
| Production UI | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Streamlit lab | http://localhost:8501 |
| iPhone test | ngrok HTTPS URL → port 3000 |
| Home API | `GET /home` |
| Net worth source | Sum of `assets.estimated_value` |

For development roadmap, see `Nextstep.md`. For architecture, see `docs/ARCHITECTURE.md`.
