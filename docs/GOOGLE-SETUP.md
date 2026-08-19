# Google Calendar + Gmail Integration Guide

WilliamOS (Mini-jarv) — setup, usage, and limitations

---

## Overview

The Google integration syncs **calendar events** into WilliamOS (`calendar_events`) and pulls **unread Gmail** into your **Inbox** as signals. The AI can create meetings with write-back to Google Calendar when connected.

**Stack:** Google Calendar API + Gmail API → FastAPI (`google_service.py`) → `calendar_events` + Inbox

**Important:** OAuth scope changed from `calendar.readonly` to `calendar.events`. **Reconnect Google** under Integrasjoner if you connected before this update.

---

## What's Already Built

The full OAuth and sync path is wired in the app:

| Layer | Status | Location |
|-------|--------|----------|
| OAuth flow | Done | `app/services/google_service.py` |
| Token refresh | Done | Auto-refreshes before sync |
| Calendar fetch | Done | Next 7 days, max 15 events |
| Gmail fetch | Done | Last 8 unread messages |
| API routes | Done | `app/api/routes/integrations.py` |
| UI | Done | `/integrations` + `/integrations/callback` |
| DB table | Done | `user_integrations` (+ migration for `google` provider) |

### OAuth flow

1. **Integrasjoner → Koble til** → `POST /integrations/google/connect`
2. Redirect to Google login
3. Google redirects to `/integrations/callback?code=...&state=...`
4. Callback calls `POST /integrations/google/complete`
5. Tokens stored in `user_integrations`

### Sync flow

1. **Synk til Inbox** → `POST /integrations/google/sync`
2. Upserts calendar into `calendar_events` + fetches unread mail
3. Gmail lines still appear in Inbox with LLM suggestions

---

## What You Need to Do

### 1. Run Supabase migrations

In Supabase SQL editor, ensure these are applied:

```
migrations/2026-08-17_finance_health_integrations.sql
migrations/2026-08-18_google_integration.sql
```

The second migration adds `google` as a valid provider in `user_integrations`.

### 2. Set up Google Cloud Console (~15 min)

Go to: https://console.cloud.google.com

1. **Create a project** (or select existing)
2. **APIs & Services → Library** — enable:
   - **Google Calendar API**
   - **Gmail API**
3. **OAuth consent screen**
   - User type: **External** (for personal Gmail) or Internal (Workspace)
   - Add your email as a **Test user** while in testing mode
   - Scopes: Calendar read-only + Gmail read-only
4. **Credentials → Create credentials → OAuth client ID**
   - Application type: **Web application**
   - **Authorized redirect URIs:**
     - Local: `http://localhost:3000/integrations/callback`
     - iPhone via ngrok: `https://YOUR-SUBDOMAIN.ngrok-free.app/integrations/callback`
5. Copy **Client ID** and **Client secret**

> **Note:** Google Cloud OAuth is free for personal/dev use. No billing required for API access at MVP scale.

### 3. Set environment variables

Add to your root `.env`:

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/integrations/callback
FRONTEND_URL=http://localhost:3000
```

**Critical:** `GOOGLE_REDIRECT_URI` must match Google Cloud **exactly** (including path `/integrations/callback`).

### 4. Restart the backend

FastAPI reads env at startup. Without restart, Integrasjoner shows "Sett GOOGLE_CLIENT_ID…" and **Koble til** stays disabled.

### 5. Connect in the app

1. Start backend (`:8000`) + frontend (`:3000`)
2. Log in to Mini-jarv
3. Go to **Mer → Integrasjoner**
4. Click **Koble til** on Google Calendar & Gmail
5. Approve Google permissions (Calendar + Gmail read)
6. Click **Synk til Inbox** → check **Inbox**

### 6. Use a Google account with calendar and mail

Works with personal `@gmail.com` and Google Workspace accounts.

---

## Required Scopes

```
https://www.googleapis.com/auth/calendar.events
https://www.googleapis.com/auth/gmail.readonly
```

Defined in `app/services/google_service.py`. OAuth uses `access_type=offline` and `prompt=consent` so a refresh token is issued on first connect.

---

## Known Limitations (Today)

| Limitation | Detail |
|------------|--------|
| Manual sync only | No cron, no sync-on-login |
| Duplicates | Re-syncing creates duplicate Inbox items |
| Unread email only | Read mail is skipped |
| Calendar window | 7 days ahead, max 15 events |
| No calendar UI | Events only appear as Inbox text lines |
| Testing mode | Only test users you add can connect until app is verified |
| No auto-tasks | Sync creates Inbox signals; tasks are not auto-created |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Sett GOOGLE_CLIENT_ID…" in UI | Env vars missing, or backend not restarted |
| Redirect URI mismatch | Google Cloud URI must equal `GOOGLE_REDIRECT_URI` exactly |
| "Ugyldig OAuth-state" | Click Koble til again |
| Koble til button disabled | `configured: false` — check env vars |
| "Access blocked" / 403 | Add your Gmail as test user on OAuth consent screen |
| ngrok on iPhone | Update both Google redirect URI and `GOOGLE_REDIRECT_URI` |
| No inbox after sync | Calendar empty next 7 days, or no unread mail |
| Token expired / error | Disconnect and reconnect Google |

---

## API Reference

All endpoints require authenticated user (Bearer JWT).

```
GET  /integrations                         List integration statuses
POST /integrations/google/connect          Start OAuth, returns auth_url
POST /integrations/google/complete         Complete OAuth with code + state
POST /integrations/google/sync             Sync calendar + mail to Inbox
POST /integrations/google/disconnect       Disconnect and clear tokens
```

---

## Pre-Flight Checklist

- [ ] Migrations `finance_health_integrations` + `google_integration` run in Supabase
- [ ] Google Calendar API and Gmail API enabled
- [ ] OAuth client created with correct redirect URI
- [ ] Your email added as test user (if app is in Testing)
- [ ] `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` in `.env`
- [ ] Backend restarted after env changes
- [ ] Logged into Mini-jarv
- [ ] Google account has upcoming events and/or unread mail

---

## Future Improvements (Not Built Yet)

- Dedup on sync (avoid duplicate Inbox rows)
- Calendar event → auto-suggest/create task
- Email keyword parsing (forsikring, faktura → asset/task)
- Auto-sync on login or scheduled daily sync
- Dedicated calendar view in the app

---

*Generated for WilliamOS / Mini-jarv — see also `docs/GETTING-STARTED.md`*
