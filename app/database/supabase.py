import base64
import json
import os
import time

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_SET_SESSION_RETRIES = 3
_SET_SESSION_RETRY_DELAY_SEC = 0.4


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


def _set_session_with_retry(client: Client, access_token: str, refresh_token: str) -> None:
    """Validate session via Supabase Auth (retries transient 5xx)."""
    last_error: Exception | None = None
    for attempt in range(_SET_SESSION_RETRIES):
        try:
            client.auth.set_session(access_token, refresh_token)
            return
        except Exception as exc:
            last_error = exc
            message = str(getattr(exc, "message", None) or exc).lower()
            retryable = "502" in message or "503" in message or "504" in message or "gateway" in message
            if not retryable or attempt >= _SET_SESSION_RETRIES - 1:
                break
            time.sleep(_SET_SESSION_RETRY_DELAY_SEC * (attempt + 1))
    if last_error is not None:
        message = str(getattr(last_error, "message", None) or last_error)
        if "502" in message or "503" in message or "504" in message or "gateway" in message.lower():
            raise RuntimeError(
                "Supabase Auth er midlertidig utilgjengelig. Prøv igjen om et øyeblikk."
            ) from last_error
        raise last_error


def get_authenticated_client(
    access_token: str,
    refresh_token: str,
    *,
    validate_session: bool = True,
) -> Client:
    """Return a Supabase client scoped to the signed-in user (RLS applies).

    Storage calls should pass validate_session=False to avoid hitting /auth/v1/user
    on every database operation — PostgREST only needs the JWT via postgrest.auth().
    """
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
    if validate_session:
        try:
            _set_session_with_retry(client, token, refresh_token.strip())
        except IndexError as exc:
            raise RuntimeError("Sesjonen er utløpt. Logg inn på nytt.") from exc
    # Ensure PostgREST uses the user JWT (RLS auth.uid() on inserts).
    client.postgrest.auth(token)
    return client


def response_data(response, default=None):
    """Safely read ``.data`` from a Supabase execute() result.

    ``maybe_single().execute()`` can return ``None`` when no row exists.
    """
    if response is None:
        return default
    data = getattr(response, "data", None)
    return default if data is None else data
