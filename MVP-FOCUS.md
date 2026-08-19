# WilliamOS — MVP Test Session

This document defines the **focused test app** — what is in scope for daily testing now.

---

## Goal

Build and test a **small, excellent** daily-use app — not the full WilliamOS platform yet.

**Core loop:**

1. Open app → see **Hjem** summary + ukens brief  
2. **Chat** with your PA (streaming, quick actions, persistent history)  
3. Capture in **Inbox** → apply AI suggestions  
4. Track **Oppgaver** (create, complete, edit) and **Eiendeler** (create, edit, detail, net worth)  
5. Adjust **Innstillinger** (assistant name, usage stats)

---

## All modules in Next.js (`web/`)

| Module | Route | Purpose |
|--------|-------|---------|
| Hjem | `/home` | Greeting, net worth, weekly brief, tappable priorities |
| Chat | `/chat` | Streaming PA, quick actions, document source chips |
| Inbox | `/inbox` | Capture + apply suggestion cards |
| Oppgaver | `/tasks` | Create, complete, edit tasks |
| Eiendeler | `/assets` | Create, edit, detail page with tasks/docs/timeline |
| Prosjekter | `/projects` | Projects + linked goals/assets |
| Mål | `/goals` | Goals by module with linked records |
| Beslutninger | `/decisions` | Decision log |
| Timeline | `/timeline` | Life events |
| Dokumenter | `/documents` | Upload + list |
| Minne | `/memory` | Save facts for PA context |
| Innstillinger | `/settings` | Profile, preferences, export, usage stats |

**Brand:** Mini-jarv (PWA icons in `web/public/`)

**Navigation:** Mobile bottom bar with full module access via «Mer» menu.

**Legacy redirects:** `/dashboard` → `/home`, `/events` → `/timeline`

---

## Definition of done (MVP test)

- [ ] Login works on Mac and iPhone (ngrok)  
- [ ] Hjem shows correct net worth + weekly brief  
- [ ] Chat streams with quick actions  
- [ ] Inbox capture + apply suggestions works  
- [ ] Task create + complete + edit works  
- [ ] Asset create + edit + detail updates Hjem net worth  
- [ ] Document upload works (asset detail or documents page)  
- [ ] Assistant name saves in settings  
- [ ] You use it daily for 7 days for core tasks  

See [docs/SEVEN-DAY-TEST.md](docs/SEVEN-DAY-TEST.md) for the daily ritual.

---

## Completed (recent)

- Asset detail page (`GET /assets/{id}`)
- Document upload in Next.js
- Persistent chat history
- Usage tracking for 7-day test
- Smarter inbox (LLM + rule fallback)

---

## Next after 7-day pass

1. Deploy (see [docs/DEPLOY.md](docs/DEPLOY.md))
2. HouseOS beta ([docs/HOUSEOS-BETA.md](docs/HOUSEOS-BETA.md))
3. Re-enable or merge Dashboard into Hjem if weekly brief isn't enough
