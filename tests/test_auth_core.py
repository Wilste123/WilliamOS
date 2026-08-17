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
