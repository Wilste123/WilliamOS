import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

import os
from supabase import create_client

def get_supabase():
    raw_url = os.getenv("SUPABASE_URL")
    raw_key = os.getenv("SUPABASE_KEY")

    print("URL present:", raw_url is not None, "len:", len(raw_url or ""))
    print("KEY present:", raw_key is not None, "len:", len(raw_key or ""))
    print("URL startswith https://:", (raw_url or "").strip().startswith("https://"))
    print("KEY has ws diff:", (raw_key or "") != (raw_key or "").strip())

    url = (raw_url or "").strip()
    key = (raw_key or "").strip()

    if not url or not key:
        return None

    return create_client(url, key)


def get_supabase() -> Client | None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key or "your_" in url or "your_" in key:
        return None
    return create_client(url, key)
