# LifeOS

## Operativsystemet for alt mennesker eier, vedlikeholder og tar beslutninger om

---

# 1. Mission

LifeOS skal bli stedet hvor mennesker organiserer, forstår og tar bedre beslutninger om alt de eier.

I dag er informasjon spredt mellom:

- mapper
- e-post
- banker
- forsikringsselskaper
- regneark
- notatapper
- hodet til brukeren

LifeOS samler dette til ett system.

# 2. Vision

Apple organiserer digitale enheter.
Microsoft organiserer arbeid.
Google organiserer informasjon.
LifeOS organiserer livet.

På lang sikt skal LifeOS være livets operativsystem for:

- bolig
- hytte
- bil
- båt
- økonomi
- dokumenter
- vedlikehold
- prosjekter
- familieverdier

# 3. North Star

Brukeren skal kunne spørre:

"Hva bør jeg gjøre denne uka?"

og få et korrekt svar.

# 4. Produktstruktur

LifeOS
- HouseOS
- VehicleOS
- CabinOS
- FinanceOS
- FamilyOS
- Future Modules

# 5. HouseOS

Første produkt.

HouseOS løser ett konkret problem:

Ingen har orden på boligen sin.

HouseOS skal samle:

- dokumenter
- vedlikehold
- forsikring
- oppgaver
- historikk
- kostnader

# 6. WilliamOS

Intern prototype.

WilliamOS er testmiljøet.

WilliamOS -> HouseOS -> LifeOS

# 7. Self-Evolve

Self-Evolve er ikke et produkt.

Self-Evolve er en motor.

Den skal:

- logge behov
- identifisere mønstre
- foreslå funksjoner
- foreslå moduler

# 8. Design Principles

## Regel 1
AI skal utføre. Ikke bare svare.

Dårlig:
"Du burde opprette en oppgave"

Bra:
"Oppgave opprettet"

## Regel 2
Alt er strukturert data.

## Regel 3
Brukeren skal ikke tenke i mapper.

# 9. Core Objects

- Asset
- Task
- Project
- Document
- Event
- Decision

# 10. Asset First Philosophy

LifeOS skal være asset-basert.

Eksempel:

Mazda CX-5
- Oppgaver
- Dokumenter
- Historikk
- Kostnader
- Hendelser
- Beslutninger

# 11. Inbox

Alt starter i Inbox.

Bruker skriver:

"Vurderer å kjøpe Pioner 320 til 25 000"

System foreslår:

- Asset: Pioner 320
- Verdi: 25 000
- Status: Vurderes kjøpt

# 12. Dashboard

Vis:

- Prioriteter
- Kommende hendelser
- Åpne oppgaver
- Aktive prosjekter
- Nye dokumenter

# 13. Timeline

Systemet bygger automatisk historikken.

# 14. Action Engine

Alle handlinger går gjennom:

- create_asset()
- update_asset()
- create_task()
- update_task()
- create_project()
- create_document()
- create_event()
- create_decision()

# 15. Tool Calling

AI returnerer strukturert handling.
Action Engine utfører.

# 16. Technology Stack

Frontend:
- Streamlit
- Senere Next.js

Backend:
- FastAPI

Database:
- Supabase
- PostgreSQL

AI:
- OpenAI

Retrieval:
- pgvector

# 17. Moat

Moaten er livshistorikken:

- eiendeler
- dokumenter
- vedlikehold
- beslutninger
- hendelser

# 18. Monetisering

Person: 99 kr/mnd

Familie: 199 kr/mnd

Premium: 299 kr/mnd

# 19. Roadmap

V1
- Chat
- Minne
- Dokumenter

V2
- Assets
- Tasks

V3
- Projects
- Dashboard

V4
- Tool Calling
- Action Engine

V5
- Timeline
- Decisions

V6
- Self-Evolve

V7
- HouseOS Launch

V8
- LifeOS

# 20. Success Metric

Målet er:

Hvor mange dager per uke åpner brukeren LifeOS?

Target: 5+

# Final Rule

Vi bygger ikke en chatbot.

Vi bygger et personlig operativsystem.
