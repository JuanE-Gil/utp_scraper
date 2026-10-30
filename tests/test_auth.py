# Task 2.0 — auth.py: login ROPC sin navegador (ADR-0007, verificado 29-oct-2026).
# Sin red: requests se mockea; las derivaciones son matemáticas puras.

import pytest

from utp_scraper.auth import AuthError, Session, derive_user_id, login
from utp_scraper.api import API_ROOT, API_BASE


# Par público, verificado en producción contra el SPA (ADR-0007).
_PAR_EMAIL = "U21320952@utp.edu.pe"
_PAR_UUID = "04aba43a-d977-5c02-9dbb-cd97ed930438"


def test_derive_user_id_not_invariant():
    assert derive_user_id(_PAR_EMAIL) == _PAR_UUID


def test_derive_user_id_ignores_mayusculas_de_email():
    # La derivación corre sobre email en mayúsculas y trimeado.
    assert derive_user_id(_PAR_EMAIL.lower()) == _PAR_UUID
    assert derive_user_id(" " + _PAR_EMAIL.upper() + " ") == _PAR_UUID


def _fake_token_response(monkeypatch, payload=None, status=200):
    """Stub de requests.post y requests.get de utp_scraper.auth."""
    import base64
    import json
    from types import SimpleNamespace

    claims = payload if payload is not None else {
        "sub": "sub-debe-ignorarse",
        "email": _PAR_EMAIL,
    }
    def b64(b):
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
    jwt = ".".join([b64(b"{}"),
                    b64(json.dumps(claims).encode()),
                    "firma"])
    token = SimpleNamespace(access_token=jwt, refresh_token="refresh-abc",
                            expires_in=86400, refresh_expires_in=90000)

    calls = []

    def fake_post(url, data=None, timeout=None):
        calls.append(("post", url, dict(data or {})))
        if status != 200:
            # respuesta con formato Keycloak: {"error": ..., "error_description": ...}
            return SimpleNamespace(
                status_code=status,
                json=lambda: {"error": "invalid_grant",
                              "error_description": "Invalid user credentials"},
            )
        return SimpleNamespace(status_code=200, json=lambda: {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_in": token.expires_in,
            "refresh_expires_in": token.refresh_expires_in,
        })

    monkeypatch.setattr("utp_scraper.auth.requests", 
                        SimpleNamespace(post=fake_post, get=lambda *a, **k: None))
    return calls


def test_login_ropc_pide_el_grant_correcto(monkeypatch):
    from utp_scraper.auth import SSO_TOKEN_URL, TENANT_ID, login

    calls = _fake_token_response(monkeypatch)
    s = login("U21320952", "clave")

    (_, url, data), = [
        ("post", u, d) for (m, u, d) in calls if m == "post"]
    assert url == SSO_TOKEN_URL
    assert data["grant_type"] == "password"
    assert data["client_id"] == "pao-web"
    assert data["username"] == "U21320952"
    assert data["password"] == "clave"
    # scope openid obligatorio (gateway, ADR-0007)
    assert "openid" in data["scope"]
    # el user-id NO es el sub del JWT: se deriva del email
    assert s.user_id == _PAR_UUID
    assert s.headers["x-tenant-id"] == TENANT_ID
    assert s.headers["authorization"].startswith("Bearer ")


def test_login_error_ofrece_descripcion(monkeypatch):
    _fake_token_response(monkeypatch, status=401)
    with pytest.raises(AuthError) as e:
        login("U21320952", "clave-mala")
    assert "invalid_grant" in str(e.value)
