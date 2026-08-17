from __future__ import annotations

from app.database.supabase import get_authenticated_client, get_supabase_anon, response_data
from app.services.auth_context import UserContext


def _build_context(
    session,
    user,
    household_id: str,
    display_name: str | None = None,
    assistant_name: str | None = None,
) -> UserContext:
    return UserContext(
        user_id=user.id,
        email=user.email or "",
        household_id=household_id,
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        display_name=display_name,
        assistant_name=assistant_name,
    )


def _extract_display_name(user) -> str | None:
    metadata = getattr(user, "user_metadata", None) or {}
    if isinstance(metadata, dict):
        name = metadata.get("display_name") or metadata.get("full_name") or metadata.get("name")
        if name:
            return str(name).strip()
    return None


def _first_row(response, default=None):
    rows = response_data(response, []) or []
    if not rows:
        return default
    return rows[0]


def _load_profile(client, user_id: str) -> dict:
    response = (
        client.table("user_profiles")
        .select("display_name, default_household_id")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return _first_row(response, {}) or {}


def _find_household_id(client, user_id: str) -> str | None:
    profile = _load_profile(client, user_id)
    if profile.get("default_household_id"):
        return profile["default_household_id"]

    membership = (
        client.table("household_members")
        .select("household_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    row = _first_row(membership)
    if row:
        return row["household_id"]
    return None


def ensure_user_provisioned(client, user, display_name: str | None = None) -> str:
    """Create household/profile/membership on first login when signup deferred setup."""
    existing = _find_household_id(client, user.id)
    if existing:
        profile = _load_profile(client, user.id)
        if not profile.get("default_household_id"):
            client.table("user_profiles").update({"default_household_id": existing}).eq("id", user.id).execute()
        return existing

    label = display_name or _extract_display_name(user) or (user.email.split("@")[0] if user.email else "Min")
    household = (
        client.table("households")
        .insert({"name": f"{label}s husholdning", "created_by": user.id})
        .execute()
    )
    household_row = _first_row(household)
    if not household_row:
        raise RuntimeError("Kunne ikke opprette husholdning ved innlogging.")
    household_id = household_row["id"]

    client.table("household_members").insert(
        {
            "household_id": household_id,
            "user_id": user.id,
            "role": "owner",
        }
    ).execute()

    profile = _load_profile(client, user.id)
    if profile:
        client.table("user_profiles").update(
            {
                "display_name": display_name or profile.get("display_name") or label,
                "default_household_id": household_id,
            }
        ).eq("id", user.id).execute()
    else:
        client.table("user_profiles").insert(
            {
                "id": user.id,
                "display_name": display_name or label,
                "default_household_id": household_id,
            }
        ).execute()

    return household_id


def sign_up(email: str, password: str, display_name: str, household_name: str) -> UserContext:
    client = get_supabase_anon()
    if client is None:
        raise RuntimeError("Supabase er ikke konfigurert.")

    auth_response = client.auth.sign_up(
        {
            "email": email.strip(),
            "password": password,
            "options": {"data": {"display_name": display_name.strip()}},
        }
    )
    if auth_response.user is None:
        raise RuntimeError("Kunne ikke opprette bruker.")

    if auth_response.session is None:
        raise RuntimeError(
            "Bruker opprettet. Bekreft e-posten din, logg deretter inn — "
            "husholdning og profil opprettes automatisk ved første innlogging."
        )

    authed = get_authenticated_client(
        auth_response.session.access_token,
        auth_response.session.refresh_token,
    )
    household_id = ensure_user_provisioned(authed, auth_response.user, display_name.strip())
    authed.table("households").update({"name": household_name.strip()}).eq("id", household_id).execute()

    return _build_context(
        auth_response.session,
        auth_response.user,
        household_id,
        display_name.strip(),
    )


def sign_in(email: str, password: str) -> UserContext:
    client = get_supabase_anon()
    if client is None:
        raise RuntimeError("Supabase er ikke konfigurert.")

    auth_response = client.auth.sign_in_with_password(
        {"email": email.strip(), "password": password}
    )
    if auth_response.session is None or auth_response.user is None:
        raise RuntimeError("Ugyldig e-post eller passord.")

    authed = get_authenticated_client(
        auth_response.session.access_token,
        auth_response.session.refresh_token,
    )
    display_name = _extract_display_name(auth_response.user)
    household_id = ensure_user_provisioned(authed, auth_response.user, display_name)
    profile = _load_profile(authed, auth_response.user.id)

    return _build_context(
        auth_response.session,
        auth_response.user,
        household_id,
        profile.get("display_name") or display_name,
    )


def build_context_from_tokens(access_token: str, refresh_token: str) -> UserContext:
    """Rebuild UserContext from stored tokens (FastAPI / Next.js clients)."""
    client = get_authenticated_client(access_token, refresh_token)
    user_response = client.auth.get_user(access_token)
    user = user_response.user if user_response else None
    if user is None:
        raise RuntimeError("Ugyldig eller utløpt sesjon.")

    display_name = _extract_display_name(user)
    household_id = _find_household_id(client, user.id)
    if not household_id:
        household_id = ensure_user_provisioned(client, user, display_name)

    profile = _load_profile(client, user.id)
    session = type("Session", (), {"access_token": access_token, "refresh_token": refresh_token})()

    return _build_context(
        session,
        user,
        household_id,
        profile.get("display_name") or display_name,
    )


def context_to_response(context: UserContext) -> dict:
    return {
        "user_id": context.user_id,
        "email": context.email,
        "household_id": context.household_id,
        "display_name": context.display_name,
        "assistant_name": context.assistant_name,
        "access_token": context.access_token,
        "refresh_token": context.refresh_token,
    }
