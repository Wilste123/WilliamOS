import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


def get_supabase() -> Client | None:
    url = os.getenv("https://srhwhyevmgxusszioxqh.supabase.co/rest/v1/")
    key = os.getenv("sb_publishable_E4UWimIWU1CfURuVI1PZqw_gUlFOfme")
    if not url or not key or "your_" in url or "your_" in key:
        return None
    return create_client(url, key)
