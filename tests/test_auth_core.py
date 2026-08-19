from app.services.auth_core import _raise_auth_error


def test_invalid_credentials_maps_to_runtime_error():
    class FakeAuthError(Exception):
        code = "invalid_credentials"
        message = "Invalid login credentials"

    try:
        _raise_auth_error(FakeAuthError())
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "Ugyldig e-post eller passord."


def test_email_not_confirmed_maps_to_runtime_error():
    class FakeAuthError(Exception):
        code = "email_not_confirmed"
        message = "Email not confirmed"

    try:
        _raise_auth_error(FakeAuthError())
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "Bekreft e-posten" in str(exc)


def test_expired_jwt_maps_to_runtime_error():
    class FakeAuthError(Exception):
        code = "bad_jwt"
        message = "invalid JWT: unable to parse or verify signature, token is expired"

    try:
        _raise_auth_error(FakeAuthError())
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert str(exc) == "Sesjonen er utløpt. Logg inn på nytt."


def test_finalize_tokens_publishes_rotated_session(monkeypatch):
    from app.services import auth_core

    published: list[tuple[str, str]] = []

    class FakeSession:
        access_token = "rotated-access"
        refresh_token = "rotated-refresh"

    class FakeAuth:
        def get_session(self):
            return FakeSession()

    class FakeClient:
        auth = FakeAuth()

        class postgrest:
            @staticmethod
            def auth(_token: str) -> None:
                return None

    monkeypatch.setattr(
        auth_core,
        "_publish_token_rotation",
        lambda original_refresh, access, refresh, **kwargs: published.append((access, refresh)),
    )

    access, refresh = auth_core._finalize_tokens(
        FakeClient(),
        "stale-access",
        "old-refresh",
        "old-refresh",
    )

    assert access == "rotated-access"
    assert refresh == "rotated-refresh"
    assert published == [("rotated-access", "rotated-refresh")]
