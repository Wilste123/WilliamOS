# WilliamOS — Deploy

Deploy after passing the local 7-day test ([docs/SEVEN-DAY-TEST.md](./SEVEN-DAY-TEST.md)).

## Architecture

```
iPhone PWA / Browser
       │
       ▼
  Vercel (Next.js)
       │  /api/* rewrite OR NEXT_PUBLIC_API_URL
       ▼
  Fly.io / Railway (FastAPI)
       │
       ▼
  Supabase (Postgres + Auth + Storage)
```

## 1. Supabase

Run all migrations in order:

- `migrations/2026-08-13_unified_storage.sql`
- `migrations/2026-08-16_auth_households.sql`
- `migrations/2026-08-16_assistant_name.sql`
- `migrations/2026-08-17_usage_log.sql`

Create Storage bucket `documents` (or value of `DOCUMENTS_BUCKET`).

## 2. FastAPI (Fly.io)

```bash
fly launch --no-deploy   # use fly.toml in repo root
fly secrets set OPENAI_API_KEY=... SUPABASE_URL=... SUPABASE_ANON_KEY=...
fly secrets set CORS_ORIGINS=https://your-app.vercel.app
fly deploy
```

Required env vars:

```bash
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
DOCUMENTS_BUCKET=documents
CORS_ORIGINS=https://your-app.vercel.app
```

Health check: `GET /health`

## 3. Next.js (Vercel)

Import `web/` as project root (or monorepo with root directory `web`).

Environment variables:

```bash
NEXT_PUBLIC_API_URL=https://your-api.fly.dev
```

If using Vercel rewrites instead, add to `vercel.json`:

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://your-api.fly.dev/:path*" }
  ]
}
```

## 4. Post-deploy

- Test login on iPhone
- Add to Home Screen
- Verify chat, inbox, asset detail, document upload
- Confirm usage tracking in Innstillinger

## 5. Rollback

- Vercel: redeploy previous deployment
- Fly: `fly releases` → rollback
