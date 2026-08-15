import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


def get_supabase() -> Client | None:
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_KEY") or "").strip()
    if not url or not key or "your_" in url or "your_" in key:
        return None
    return create_client(url, key)
