import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


def _get_supabase_url() -> str | None:
    url = (os.getenv("SUPABASE_URL") or "").strip()
    if not url or "your_" in url:
        return None
    return url


def _get_supabase_anon_key() -> str | None:
    key = (os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY") or "").strip()
    if not key or "your_" in key:
        return None
    return key


def get_supabase_anon() -> Client | None:
    """Return an anonymous Supabase client for auth flows."""
    url = _get_supabase_url()
    key = _get_supabase_anon_key()
    if not url or not key:
        return None
    return create_client(url, key)


def get_supabase() -> Client | None:
    """Backward-compatible alias used by tests and legacy callers."""
    return get_supabase_anon()


def get_authenticated_client(access_token: str, refresh_token: str) -> Client:
    """Return a Supabase client scoped to the signed-in user (RLS applies)."""
    client = get_supabase_anon()
    if client is None:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables."
        )
    client.auth.set_session(access_token, refresh_token)
    return client


def response_data(response, default=None):
    """Safely read ``.data`` from a Supabase execute() result.

    ``maybe_single().execute()`` can return ``None`` when no row exists.
    """
    if response is None:
        return default
    data = getattr(response, "data", None)
    return default if data is None else data
