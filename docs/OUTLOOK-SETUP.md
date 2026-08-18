# Outlook / Calendar Integration Guide

WilliamOS (Mini-jarv) — setup, usage, and limitations

---

## Overview

The Outlook/calendar integration pulls **calendar events** and **unread emails** from Microsoft Outlook into your **Inbox** as signals. You can then apply AI suggestions to create tasks, assets, and more.

**Stack:** Microsoft Graph API → FastAPI (`outlook_service.py`) → Inbox (`capture_inbox_entry`)

---

## What's Already Built

You do **not** need to write integration code — the full path is wired:

| Layer | Status | Location |
|-------|--------|----------|
| OAuth flow | Done | `app/services/outlook_service.py` |
| Token refresh | Done | Auto-refreshes before sync |
| Calendar fetch | Done | Next 7 days, max 15 events |
| Email fetch | Done | Last 8 messages, unread only |
| API routes | Done | `app/api/routes/integrations.py` |
| UI | Done | `/integrations` + `/integrations/callback` |
| DB table | Done | `user_integrations` in migration |

### OAuth flow

1. **Integrasjoner → Koble til** → `POST /integrations/outlook/connect`
2. Redirect to Microsoft login
3. Microsoft redirects to `/integrations/callback?code=...&state=...`
4. Callback calls `POST /integrations/outlook/complete`
5. Tokens stored in `user_integrations`

### Sync flow

1. **Synk til Inbox** → `POST /integrations/outlook/sync`
2. Fetches calendar + unread mail via Microsoft Graph
3. Creates Inbox lines like:
   - `Outlook kalender: Møte (2026-08-18 10:00)`
   - `Outlook e-post: Forsikring fornyes`
4. Each line gets LLM/rule-based suggestions — you apply them manually in Inbox

---

## What You Need to Do

### 1. Run the Supabase migration

In Supabase SQL editor, run:

```
migrations/2026-08-17_finance_health_integrations.sql
```

This creates the `user_integrations` table where OAuth tokens are stored.

### 2. Register a free Azure app (~15 min)

Go to: https://portal.azure.com → **App registrations**

1. **New registration**
2. **Redirect URI (Web):**
   - Local: `http://localhost:3000/integrations/callback`
   - iPhone via ngrok: `https://YOUR-SUBDOMAIN.ngrok-free.app/integrations/callback`
3. **Certificates & secrets** → create a **Client secret** (copy immediately)
4. **API permissions** → Microsoft Graph → **Delegated**:
   - `Calendars.Read`
   - `Mail.Read`
   - `User.Read`
   - `offline_access` (for refresh token)
5. **Grant admin consent** if your tenant requires it

> **Note:** This is free — no paid Azure subscription needed.

### 3. Set environment variables

Add to your root `.env`:

```bash
MICROSOFT_CLIENT_ID=your-app-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_REDIRECT_URI=http://localhost:3000/integrations/callback
FRONTEND_URL=http://localhost:3000
```

**Critical:** `MICROSOFT_REDIRECT_URI` must match Azure **character for character**.

### 4. Restart the backend

FastAPI reads env at startup. Without restart, the Integrations page shows "Sett MICROSOFT_CLIENT_ID…" and the connect button stays disabled.

### 5. Connect in the app

1. Start backend (`:8000`) + frontend (`:3000`)
2. Log in to Mini-jarv
3. Go to **Mer → Integrasjoner**
4. Click **Koble til** on Outlook → Microsoft login → approve
5. Click **Synk til Inbox** → check **Inbox**

### 6. Use a Microsoft account with calendar/email

Personal `@outlook.com` / `@hotmail.com` or work Microsoft 365 both work via the `/common` OAuth endpoint.

---

## Required Scopes

```
offline_access Calendars.Read Mail.Read User.Read
```

Defined in `app/services/outlook_service.py`.

---

## Known Limitations (Today)

| Limitation | Detail |
|------------|--------|
| Manual sync only | No cron, no sync-on-login |
| Duplicates | Re-syncing creates duplicate Inbox items |
| Unread email only | Read mail is skipped |
| Calendar window | 7 days ahead, max 15 events |
| No calendar UI | Events only appear as Inbox text lines |
| Gmail/iCloud | Not supported — Microsoft Graph only |
| Work/school tenants | May need admin consent for Mail.Read |
| No auto-tasks | Sync creates Inbox signals; tasks are not auto-created |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Sett MICROSOFT_CLIENT_ID…" in UI | All three env vars missing, or backend not restarted |
| Redirect URI mismatch | Azure URI must equal `MICROSOFT_REDIRECT_URI` exactly |
| "Ugyldig OAuth-state" | Click Koble til again (state stored in `user_integrations.metadata`) |
| Koble til button disabled | `configured: false` — check env vars |
| ngrok on iPhone | Update both Azure redirect URI and `MICROSOFT_REDIRECT_URI` to ngrok URL |
| No inbox after sync | Calendar may be empty next 7 days, or all mail is read |
| Token expired / error status | Disconnect and reconnect Outlook |

---

## API Reference (Optional)

All endpoints require authenticated user (Bearer JWT).

```
GET  /integrations                          List integration statuses
POST /integrations/outlook/connect          Start OAuth, returns auth_url
POST /integrations/outlook/complete         Complete OAuth with code + state
POST /integrations/outlook/sync             Sync calendar + mail to Inbox
POST /integrations/outlook/disconnect       Disconnect and clear tokens
```

---

## Pre-Flight Checklist

- [ ] Migration `2026-08-17_finance_health_integrations.sql` run in Supabase
- [ ] Azure app registered with correct redirect URI
- [ ] `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_REDIRECT_URI` in `.env`
- [ ] Backend restarted after env changes
- [ ] Logged into Mini-jarv
- [ ] Outlook account has upcoming calendar events and/or unread mail

---

## Future Improvements (Not Built Yet)

- Dedup on sync (avoid duplicate Inbox rows)
- Calendar event → auto-suggest/create task
- Email keyword parsing (forsikring, faktura → asset/task)
- Auto-sync on login or scheduled daily sync
- Dedicated calendar view in the app

---

*Generated for WilliamOS / Mini-jarv — see also `docs/GETTING-STARTED.md` and `MVP-FOCUS.md`*
