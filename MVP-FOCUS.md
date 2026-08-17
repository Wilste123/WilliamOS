# WilliamOS — MVP Test Session

This document defines the **focused test app** — what is in scope for daily testing now.

---

## Goal

Build and test a **small, excellent** daily-use app — not the full WilliamOS platform yet.

**Core loop:**

1. Open app → see **Hjem** summary + ukens brief  
2. **Chat** with your PA (streaming, quick actions, session history)  
3. Capture in **Inbox** → apply AI suggestions  
4. Track **Oppgaver** (create, complete, edit) and **Eiendeler** (create, edit, net worth)  
5. Adjust **Innstillinger** (assistant name)

---

## Visible in Next.js (`web/`)

| Module | Route | Purpose |
|--------|-------|---------|
| Hjem | `/home` | Greeting, net worth, weekly brief, tappable priorities |
| Chat | `/chat` | Streaming PA, quick actions, document source chips |
| Inbox | `/inbox` | Capture + apply suggestion cards |
| Oppgaver | `/tasks` | Create, complete, edit tasks |
| Eiendeler | `/assets` | Create, edit assets (feeds net worth) |
| Innstillinger | `/settings` | Assistant name |

**Brand:** Mini-jarv (PWA icons in `web/public/`)

**Navigation:** Lucide icons · Mobile bottom bar: Hjem · Chat · Inbox · Oppgaver · Mer

---

## Hidden during MVP (lab only)

Dashboard, Prosjekter, Beslutninger, Hendelser, Dokumenter, Timeline, Minne, self-evolve

Use **Streamlit** for full module access during development.

---

## Definition of done (MVP test)

- [ ] Login works on Mac and iPhone (ngrok)  
- [ ] Hjem shows correct net worth + weekly brief  
- [ ] Chat streams with quick actions  
- [ ] Inbox capture + apply suggestions works  
- [ ] Task create + complete + edit works  
- [ ] Asset create + edit updates Hjem net worth  
- [ ] Assistant name saves in settings  
- [ ] You use it daily for 7 days without Streamlit for core tasks  

---

## Next session priorities

1. Asset detail page (`GET /assets/{id}`)  
2. Re-enable Dashboard or merge into Hjem  
3. Documents upload in Next.js  
