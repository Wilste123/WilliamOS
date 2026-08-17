# 7-day daily-use test

This is the real milestone before deploy or HouseOS beta.

## Rules

1. Use **Next.js Mini-jarv only** for core tasks — no Streamlit
2. Open the app at least once per day
3. Log friction in Notes (one line per day)

## Daily ritual

**Morning (2 min)**

- Open Hjem → read ukens brief
- Tap a priority → Chat with context

**During the day**

- Capture anything new in Inbox (not Apple Notes)
- Complete tasks, update assets via app or chat

**Evening (2 min)**

- Process one inbox item (apply suggestion)

## Track progress

Open **Innstillinger** → **7-dagers test** section:

- Days opened this week
- Streak
- Total opens
- 7-day goal met (7 unique days)

## Decision gate (day 7)

| Outcome | Next move |
|---------|-----------|
| 5+ days, core loop works | Deploy + Chief of Staff depth |
| 2–4 days, friction found | Fix top 1–2 blockers only |
| 0–1 days | Simplify — remove a module |

## Questions to answer honestly

- Did I reach for Streamlit? → Fix that gap
- Did Chat save me time? → Improve tool-calling, not UI polish
- Did Hjem answer "what matters this week?" → Fix weekly brief

## Seed data (optional)

```bash
# After first login, set in .env:
# SEED_USER_ID=...
# SEED_HOUSEHOLD_ID=...
python3 scripts/seed_demo_data.py
```
