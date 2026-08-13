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
2. Legg inn API-nøkler
3. Installer avhengigheter
4. Kjør Streamlit eller FastAPI

```bash
pip install -r requirements.txt
streamlit run frontend/streamlit_app.py
```

eller:

```bash
uvicorn app.api.main:app --reload
```

## Foreslått rekkefølge

1. Chat
2. Oppgaver
3. Prosjekter
4. Eiendeler
5. Dokumenter
6. Requests-logg
7. Første HouseOS-modul
8. self-evolve dashboard

## Viktig regel

Dette skal ikke bli komplisert for tidlig. Første versjon skal bare være nyttig nok til at den brukes hver dag.
