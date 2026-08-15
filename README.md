# WilliamOS

WilliamOS er en personlig AI-assistent og prototypen til HouseOS, LifeOS og self-evolve.

Målet er å bygge en mini-Jarvis som kan brukes daglig til å holde oversikt over oppgaver, prosjekter, eiendeler, dokumenter og beslutninger.

## Konsept

- **WilliamOS** = personlig PA-agent og testlab
- **HouseOS** = første eksterne produkt, med bolig, dokumenter og eiendeler
- **LifeOS** = langsiktig visjon, et operativsystem for alt man eier og må følge opp
- **self-evolve** = motoren som logger brukerbehov og foreslår nye funksjoner

## Teknologi

- Python
- FastAPI
- Streamlit
- Supabase
- OpenAI API
- pgvector senere

## Første milepæl

Bruk systemet daglig i 30 dager.

Hvis du faktisk bruker det, bygger vi videre.
Hvis du ikke bruker det, forenkler vi.

## Kom i gang

1. Kopier `.env.example` til `.env`
2. Legg inn API-nøkler for OpenAI og Supabase
3. Installer avhengigheter
4. Kjør Streamlit eller FastAPI

Påkrevde miljøvariabler:

```bash
OPENAI_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
DOCUMENTS_BUCKET=documents
```

`DOCUMENTS_BUCKET` er valgfri og bruker `documents` som standard hvis den ikke er satt. Hvis Supabase ikke er konfigurert riktig, feiler appen tydelig i stedet for å bruke lokal fallback.

```bash
pip install -r requirements.txt
python run.py
```

eller:

```bash
streamlit run frontend/streamlit_app.py
```

eller:

```bash
uvicorn app.api.main:app --reload
```

## Hva som er bygget nå

- Inbox for å fange opp nye ting brukeren vurderer eller må følge opp
- Dashboard med prioriteringer, hendelser, dokumenter og aktivitet
- Asset-first visning med eiendeler, prosjekter, oppgaver og beslutninger
- Timeline/historikk via hendelser som bygges automatisk når data opprettes
- Supabase som eneste lagringslag — operasjoner feiler tydelig hvis Supabase ikke er konfigurert
- Dokumenter lagres i Supabase Storage-bucketen konfigurert via `DOCUMENTS_BUCKET` (standard: `documents`)
- Chat som kan utføre enkle handlinger direkte, som å opprette oppgave, eiendel, prosjekt eller beslutning

## Supabase Storage-oppsett for dokumenter

Opprett en bucket i Supabase Storage med navnet du bruker i `DOCUMENTS_BUCKET` (standard: `documents`).

- Servernøkkelen eller nøkkelen appen bruker må ha tilgang til å laste opp, lese, liste og slette objekter i bucketen.
- Hvis du bruker RLS/policies for Storage, legg til policies som tillater disse operasjonene for rollen knyttet til `SUPABASE_KEY`.

Migrasjonsnotat: dokumentenes `storage_path` peker nå til objektstien i Supabase Storage, ikke til en lokal filsti på disk.

## Foreslått rekkefølge

1. Chat
2. Oppgaver
3. Prosjekter
4. Eiendeler
5. Dokumenter
6. Requests-logg
7. Første HouseOS-modul
8. self-evolve dashboard

## Arkitektur

WilliamOS er strukturert i fire lag for å gjøre det enkelt å migrere bort fra Streamlit til en mer tilpasset webapp senere.

```
frontend/           ← UI-lag (Streamlit-spesifikt)
  streamlit_app.py  ← tynn entrypoint: konfig + navigasjon + dispatch
  ui/               ← én render_<side>() per side
  components/       ← gjenbrukbare Streamlit-hjelpere

app/services/       ← service-lag (ingen Streamlit-imports)
app/agents/         ← agent-lag (ingen Streamlit-imports)
app/database/       ← infrastruktur-lag (Supabase, OpenAI)
app/models/         ← rene datamodeller
app/api/            ← FastAPI-entrypoint (parallelt med UI-laget)
```

**Importretningsregel:** `frontend/ → app/services/ → app/database/`.
Importer går bare nedover — aldri oppover.

Se [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for full dokumentasjon,
inkludert hvordan du legger til nye funksjoner uten å koble deg til Streamlit.

## Viktig regel

Dette skal ikke bli komplisert for tidlig. Første versjon skal bare være nyttig nok til at den brukes hver dag.
