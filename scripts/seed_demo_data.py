#!/usr/bin/env python3
"""Seed demo data for the 7-day daily-use test.

Requires Supabase configured in .env and migrations applied.
Run after logging in once (or set SEED_USER_ID + SEED_HOUSEHOLD_ID in .env).

Usage:
  python3 scripts/seed_demo_data.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.services.action_engine import capture_inbox_entry, create_asset, create_task
from app.services.auth_context import UserContext, set_current_context


def main() -> None:
    user_id = os.getenv("SEED_USER_ID")
    household_id = os.getenv("SEED_HOUSEHOLD_ID")
    if not user_id or not household_id:
        print(
            "Set SEED_USER_ID and SEED_HOUSEHOLD_ID in .env "
            "(copy from Supabase auth.users + households after first login)."
        )
        sys.exit(1)

    set_current_context(
        UserContext(
            user_id=user_id,
            email=os.getenv("SEED_EMAIL", "seed@example.com"),
            household_id=household_id,
            access_token="seed",
            refresh_token="seed",
            display_name=os.getenv("SEED_DISPLAY_NAME", "William"),
        )
    )

    home = create_asset(
        {
            "name": "Tun32",
            "type": "Bolig",
            "status": "active",
            "estimated_value": 6_200_000,
            "description": "Hjemmeadresse",
        }
    )
    car = create_asset(
        {
            "name": "Mazda CX-5",
            "type": "Bil",
            "status": "active",
            "estimated_value": 350_000,
        }
    )

    create_task(
        {
            "title": "Bestill service på Mazda",
            "priority": 3,
            "status": "open",
            "asset_id": car["id"],
        }
    )
    create_task(
        {
            "title": "Sjekk forsikring Tun32",
            "priority": 2,
            "status": "open",
            "asset_id": home["id"],
        }
    )
    create_task(
        {
            "title": "Oppdater ukens prioriteringer",
            "priority": 2,
            "status": "open",
        }
    )

    capture_inbox_entry("Vurderer å kjøpe Pioner 320 til 25000")

    print("Seeded:")
    print(f"  - Assets: {home['name']}, {car['name']}")
    print("  - 3 tasks")
    print("  - 1 inbox capture")
    print("Open /home in Mini-jarv to verify net worth and weekly brief.")


if __name__ == "__main__":
    main()
