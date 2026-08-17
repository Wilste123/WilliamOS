import base64
import json
import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


def _decode_jwt_role(token: str) -> str | None:
    try:
        parts = (token or "").split(".")
        if len(parts) < 2:
            return None
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        role = data.get("role")
        return str(role) if role is not None else None
    except (ValueError, json.JSONDecodeError):
        return None


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
    token = (access_token or "").strip()
    if token.count(".") < 2:
        raise RuntimeError("Sesjonen er utløpt. Logg inn på nytt.")
    if _decode_jwt_role(token) == "service_role":
        raise RuntimeError(
            "SUPABASE_ANON_KEY must be the anon key, not the service role key. "
            "Service role bypasses row-level security."
        )
    if not (refresh_token or "").strip():
        raise RuntimeError("Sesjonen er utløpt. Logg inn på nytt.")
    try:
        client.auth.set_session(token, refresh_token.strip())
    except IndexError as exc:
        raise RuntimeError("Sesjonen er utløpt. Logg inn på nytt.") from exc
    return client


def response_data(response, default=None):
    """Safely read ``.data`` from a Supabase execute() result.

    ``maybe_single().execute()`` can return ``None`` when no row exists.
    """
    if response is None:
        return default
    data = getattr(response, "data", None)
    return default if data is None else data
