# WilliamOS — Next Steps

Dette dokumentet beskriver hva **du** må gjøre for å kjøre og videreutvikle WilliamOS etter arkitekturmigreringen (FastAPI + Next.js).

---

## 1. Kjør migrasjoner i Supabase (hvis ikke gjort)

I Supabase SQL Editor:

```sql
-- Auth + households
-- Kjør: migrations/2026-08-16_auth_households.sql

-- Assistant name (valgfritt, for egendefinert assistentnavn)
-- Kjør: migrations/2026-08-16_assistant_name.sql
```

---

## 2. Miljøvariabler

**Backend** (`.env` i repo-root):

```bash
OPENAI_API_KEY=...
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
DOCUMENTS_BUCKET=documents
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Frontend** (`web/.env.local`):

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 3. Start backend (FastAPI)

```bash
pip install -r requirements.txt
uvicorn app.api.main:app --reload --port 8000
```

Sjekk:

- http://localhost:8000/health
- http://localhost:8000/docs (OpenAPI)

---

## 4. Start Next.js frontend

```bash
cd web
npm install
npm run dev
```

Åpne: http://localhost:3000

Første gang: opprett konto eller logg inn. Hvis Supabase krever e-postbekreftelse, bekreft e-post og logg inn — husholdning opprettes automatisk.

---

## 5. Streamlit (prototype / lab)

Streamlit kjører fortsatt parallelt for testing:

```bash
streamlit run frontend/streamlit_app.py
```

**Ikke bygg nye produksjonsfeatures i Streamlit.** Bruk `web/` fremover.

---

## 6. Hva er bygget nå (Phase 2–3 start)

| Lag | Status |
|-----|--------|
| `app/services/auth_core.py` | UI-agnostisk auth (delt av Streamlit + API) |
| `app/api/deps.py` | JWT auth middleware (`Authorization` + `X-Refresh-Token`) |
| `app/api/routes/auth.py` | `/auth/login`, `/auth/signup`, `/auth/me` |
| Alle API-ruter | Krever auth (unntatt `/`, `/health`, `/auth/*`) |
| `web/` | Next.js + Tailwind, mobile-first layout |
| Sider | Login, Chat, Inbox, Dashboard |
| PWA | Grunnleggende manifest (ikoner mangler) |

---

## 7. Dine neste utviklingssteg (anbefalt rekkefølge)

### A. Lokal verifisering (du, nå)

- [ ] Kjør Supabase-migrasjoner
- [ ] `npm install` i `web/`
- [ ] Start FastAPI + Next.js
- [ ] Logg inn og test chat, inbox, dashboard
- [ ] Verifiser at Streamlit fortsatt fungerer parallelt

### B. UI polish (Phase 3)

- [ ] Kjør `npx shadcn@latest init` i `web/` og legg til Button, Input, Card, Sheet
- [ ] Lag PWA-ikoner (`web/public/icon-192.png`, `icon-512.png`)
- [ ] Forbedre dashboard-visning (kort, ikke rå JSON)
- [ ] Legg til settings-side (assistentnavn via API)

### C. API utvidelse (Phase 2 fortsettelse)

- [ ] `PATCH /auth/profile` — display name, assistant name
- [ ] `POST /chat/stream` — SSE streaming for chat
- [ ] Inbox apply-suggestion endpoint
- [ ] Tasks / assets / projects CRUD-sider i Next.js
- [ ] OpenAPI → generert TypeScript-klient (`openapi-typescript`)

### D. Deploy (når lokal flyt fungerer)

- [ ] Deploy FastAPI til Fly.io eller Railway (EU)
- [ ] Deploy Next.js til Vercel
- [ ] Sett `CORS_ORIGINS` og `NEXT_PUBLIC_API_URL` til prod-URLer
- [ ] Test PWA «Legg til på hjemskjerm» på iPhone

### E. Senere (Phase 5–6)

- [ ] Service worker for offline shell
- [ ] Capacitor wrapper når du vil ha App Store
- [ ] Fjern eller begrens Streamlit til intern lab

---

## 8. Arkitekturregler å huske

- **Next.js** = kun UI. Ingen business logic. Ingen direkte Supabase/OpenAI.
- **FastAPI** = eneste API for alle klienter.
- **Python services** = hjernen. Ny funksjon starter alltid her + tester.
- **Streamlit** = midlertidig. Ikke invester mer enn nødvendig.

Se også:

- [`docs/ARCHITECTURE-vision.md`](docs/ARCHITECTURE-vision.md) — målarkitektur
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — utviklerreferanse

---

## 9. Feilsøking

| Problem | Løsning |
|---------|---------|
| `401` på API-kall | Sjekk at du er innlogget; tokens i localStorage |
| CORS-feil | Sjekk `CORS_ORIGINS` i `.env` |
| `assistant_name does not exist` | Kjør assistant_name-migrasjon i Supabase |
| Chat feiler | Sjekk `OPENAI_API_KEY` og at FastAPI kjører |
| Next.js bygger ikke | Kjør `npm install` i `web/` |

---

## 10. Commit / push

Når du har verifisert lokalt:

```bash
git add app/ web/ tests/ Nextstep.md .env.example
git commit -m "Start Next.js frontend and FastAPI auth layer"
git push
```

(Ekskluder `.env`, `.DS_Store`, og `prompts/pa_system_prompt.txt` med mindre du vil committe dem.)
