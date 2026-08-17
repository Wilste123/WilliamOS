# WilliamOS — MVP Test Session

This document defines the **focused test app** — what is in scope for daily testing now, and what is hidden until the core experience is solid.

Use this as the brief when starting a new dev/test session.

---

## Goal

Build and test a **small, excellent** daily-use app — not the full WilliamOS platform yet.

**Core loop:**

1. Open app → see **Hjem** summary  
2. **Chat** with your PA (streaming)  
3. Capture in **Inbox**  
4. Track **Oppgaver** and **Eiendeler** (create + list; net worth on home)  
5. Adjust **Innstillinger** (assistant name)

---

## Visible in Next.js (`web/`)

| Module | Route | Purpose |
|--------|-------|---------|
| Hjem | `/home` | Greeting, net worth, priorities, empty-state CTAs |
| Chat | `/chat` | Talk to PA (SSE streaming) |
| Inbox | `/inbox` | Capture items |
| Oppgaver | `/tasks` | Task list + create form (title, optional due date) |
| Eiendeler | `/assets` | Assets + create form (name, estimated value) |
| Innstillinger | `/settings` | Assistant name |

**Navigation:**

- Sidebar (desktop) / menu drawer (mobile): **Hoved** + collapsible **Mer**
- Mobile bottom bar: Hjem · Chat · Inbox · Oppgaver · Mer

---

## Hidden during MVP (lab only)

These routes still work if you type the URL, but they are **not linked** in the UI:

- Dashboard, Prosjekter, Beslutninger, Hendelser  
- Dokumenter, Timeline, Minne, self-evolve  

Use **Streamlit** (`streamlit run frontend/streamlit_app.py`) for full module access during development.

To show a hidden module again later, add it back in `web/src/lib/navigation.ts`.

---

## Out of scope for this session

- Edit/complete forms (create-only on Oppgaver and Eiendeler)  
- PWA icons and polish  
- Capacitor / App Store  
- New backend modules  
- Finance / goals tables (goals count on home stays 0 until `goals` table exists)

---

## Definition of done (MVP test)

- [ ] Login works on Mac and iPhone (ngrok)  
- [ ] Hjem shows correct net worth from asset `estimated_value`  
- [ ] Chat answers with your data context (streaming)  
- [ ] Inbox capture works  
- [ ] Task create + list works  
- [ ] Asset create updates Hjem net worth  
- [ ] Assistant name saves in settings  
- [ ] You use it daily for 7 days without switching to Streamlit for core tasks  

---

## Done this session

1. **Task create** — simple form on Oppgaver page  
2. **Asset create** — name + estimated value (feeds Hjem net worth)  
3. **Home polish** — skeleton loading, empty states  
4. **Chat streaming** — SSE from FastAPI (`POST /chat/stream`)

## Next session priorities (suggested order)

1. **Re-enable modules one by one** — Dashboard → Documents → Projects  
2. Complete/edit task from Oppgaver  
3. Asset type / description fields  

See also: `STARTUP-INSTRUCTIONS.md`, `Nextstep.md`, `docs/ARCHITECTURE-vision.md`.
