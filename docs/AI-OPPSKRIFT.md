# AI-oppskrift — WilliamOS / Mini-jarv

Steg-for-steg guide for å ta i bruk den nye AI-motoren (alle faser).

---

## 1. Miljøvariabler (`.env` i repo-root)

Kopier fra `.env.example` og fyll inn:

| Variabel | Påkrevd | Formål |
|----------|---------|--------|
| `OPENAI_API_KEY` | Ja (for smart AI) | Chat, oppdrag, minne, embeddings |
| `OPENAI_MODEL` | Nei (default `gpt-4o-mini`) | Daglig chat |
| `OPENAI_MODEL_PLANNER` | Nei (default `gpt-4o`) | Komplekse oppdrag og lange forespørsler |
| `OPENAI_EMBEDDING_MODEL` | Nei (default `text-embedding-3-small`) | Semantisk dokumentsøk |
| `SUPABASE_URL` | Ja | Database + auth |
| `SUPABASE_ANON_KEY` | Ja | Frontend/backend mot Supabase |
| `SERPER_API_KEY` | Anbefalt | Nettsøk i chat |
| `GOOGLE_CLIENT_ID` / `SECRET` | Valgfritt | Kalender + Gmail |

Etter endring i `.env`: **restart FastAPI** (`uvicorn app.api.main:app --reload --port 8000`).

---

## 2. Database-migrasjoner (Supabase SQL Editor)

Kjør i rekkefølge hvis du ikke har kjørt dem fra før:

1. `migrations/2026-08-20_calendar_events.sql` — kalender
2. `migrations/2026-08-19_memory_preferences.sql` — preferanser (inbox_automation)
3. `migrations/2026-08-21_document_embeddings.sql` — **ny:** semantisk dokumentsøk

Sjekk at tabellen `documents` har kolonnene `embedding`, `embedding_model`, `embedded_at`.

---

## 3. Start appen

```bash
# Terminal 1 — backend
cd /path/to/WilliamOS-afui
uvicorn app.api.main:app --reload --port 8000

# Terminal 2 — frontend
cd web
npm run dev
```

Åpne http://localhost:3000 og logg inn.

Hvis frontend henger etter deploy: `rm -rf web/.next && npm run dev`.

---

## 4. Google-integrasjon (anbefalt)

1. Gå til **Integrasjoner** i appen
2. Koble til Google
3. Hvis du koblet til før kalender-skrivefix: trykk **«Oppdater Google-tilgang»**
4. Synk kalender (Integrasjoner eller Kalender-siden)

Uten Google fungerer AI fortsatt — kalender blir da kun intern.

---

## 5. Indekser dokumenter for semantisk søk (Fase 4)

**Automatisk:** Nye opplastinger indekseres ved upload (krever `OPENAI_API_KEY`).

**Eksisterende dokumenter:** Kall én gang etter migrasjon:

```bash
curl -X POST http://localhost:8000/documents/reindex-embeddings \
  -H "Authorization: Bearer <access_token>" \
  -H "X-Refresh-Token: <refresh_token>"
```

Eller via Swagger: http://localhost:8000/docs → `POST /documents/reindex-embeddings`

Uten OpenAI-nøkkel faller dokumentsøk tilbake til keyword-søk (som før).

---

## 6. Slik bruker du AI nå

### Proaktiv Chief of Staff (Hjem)
- Åpne **Hjem** → se «Forslag fra Mini-jarv»
- Forslag kommer fra: forfalte oppgaver, inbox, kommende kalender
- Trykk **Utfør** eller **Utfør alle**

### Chat med bekreftelse (Proposal mode)
- «Lag oppgave: ring rørlegger, frist fredag» → **gule knapper** → Utfør
- Create/update/delete lagres **ikke** før du godkjenner
- Minne, fullfør oppgave og inbox-capture kjører fortsatt med en gang

### Oppdrag (Mission mode)
Skriv i chat:
```
oppdrag: Forbered hyttetur neste helg
oppdrag: Håndter forsikring for hytta
```
→ Plan med flere steg → godkjenn hver handling (eller «Utfør alle»).

API: `POST /missions/plan` med `{ "goal": "..." }`.

### Dokumentspørsmål
- Last opp PDF/forsikring under **Dokumenter**
- Spør i chat: «Hva står om taket i hytteforsikringen?»
- Semantisk søk finner relevant innhold selv uten eksakte søkeord

---

## 7. Verifiser at alt fungerer (sjekkliste)

- [ ] Chat svarer ( ikke «OpenAI er ikke konfigurert» )
- [ ] «Lag oppgave …» viser gul action card → Utfør → oppgave i **Oppgaver**
- [ ] Hjem viser forslag (krever data: inbox, overdue, eller kalender)
- [ ] `oppdrag: …` gir plan med flere knapper
- [ ] Dokumentopplasting + spørsmål om innhold gir svar med dokumentkilde
- [ ] Google-kalender: app → Google og Google → app (hvis tilkoblet)

Kjør tester lokalt:
```bash
python3 -m pytest tests/ -q
```

---

## 8. Feilsøking

| Symptom | Løsning |
|---------|---------|
| «Sesjonen er utløpt» | Logg ut og inn igjen |
| Loading henger | Hard refresh; sjekk at backend kjører på :8000 |
| Ingen action cards | Sjekk `OPENAI_API_KEY`; muterende tools krever godkjenning |
| Dokumentsøk svakt | Kjør `POST /documents/reindex-embeddings` |
| Google sync en vei | Reconnect Google med skrivetilgang (Integrasjoner) |
| `Cannot find module './884.js'` | `rm -rf web/.next && npm run dev` |

---

## 9. Hva som er implementert (alle faser)

| Fase | Funksjon |
|------|----------|
| 1 | Proposal mode, `/actions/execute`, utvidede verktøy, modell-routing |
| 2 | `GET /daily-brief`, proaktive forslag på Hjem, auto-inbox-forslag |
| 3 | Oppdrag (`oppdrag:` + `/missions/plan`), LLM-planlegger med regel-fallback |
| 4 | Embeddings + hybrid dokumentsøk, entity graph i agent-kontekst, intent routing |

---

## 10. Anbefalt daglig rutine (7-dagers test)

1. **Morgen:** Åpne Hjem → utfør 1–3 forslag
2. **Under dagen:** Fang ting i Inbox eller chat (`fang i innboks …`)
3. **Oppdrag:** Bruk `oppdrag:` for større ting (hytte, forsikring, møter)
4. **Kveld:** Spør «Hva bør jeg gjøre i morgen?» i chat

Mål: AI skal **utføre** (med ditt OK), ikke bare chatte.
