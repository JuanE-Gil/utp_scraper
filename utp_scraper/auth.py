# utp_scraper.auth — login institucional sin navegador (capa api, INFORME §4).
# ADR-0007 (29-oct-2026): password grant (ROPC) contra el realm Xpedition de
# Keycloak con client pao-web, verificado fin a fin contra producción.
# Secretos: AUTH_TOKEN y contraseña (regla de credenciales, AGENTS.md).
# user-id y tenant NO son secretos: primero se deriva de `email` (JWT),
# segundo es constante pública del front (rfc4122 vendido en el SPA).

import base64
import json
import uuid
from dataclasses import dataclass

import requests

from .api import build_headers

SSO_TOKEN_URL = "https://sso.utp.edu.pe/auth/realms/Xpedition/protocol/openid-connect/token"
SSO_CLIENT_ID = "pao-web"
SCOPE = "openid roles-client-pao-web profile email roles-realm-xpedition"
TENANT_ID = "a5f469d2-3c0e-5c68-8d32-5265923a8e40"  # constante pública del front


class AuthError(Exception):
    """Fallo de autenticación (credenciales, red o config del proveedor)."""


@dataclass
class Session:
    """Sesión autenticada en memoria. Nunca serializar a disco."""
    access_token: str
    refresh_token: str
    user_id: str
    expires_in: int
    refresh_expires_in: int

    @property
    def headers(self) -> dict:
        return build_headers(self.access_token, self.user_id, TENANT_ID)


def derive_user_id(email: str) -> str:
    """user-id real de la API = uuid5(NAMESPACE_DNS, email_MAYUSCULA).

    Verificado contra producción y el source del SPA (ADR-0007).
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, email.strip().upper()))


def _decode_jwt(token: str) -> dict:
    head, payload, _ = token.split(".")
    payload += "=" * ((4 - len(payload) % 4) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def _post(keycloak_data: dict) -> "Session":
    try:
        r = requests.post(SSO_TOKEN_URL, data=keycloak_data, timeout=30)
    except requests.RequestException as e:
        raise AuthError(f"sin conexión con el servidor de identidad: {e}") from e
    if r.status_code != 200:
        detail = ""
        try:
            body = r.json()
            # formato Keycloak催眠: {"error": "...", "error_description": "..."}
            detail = f"{body.get('error', '')} {body.get('error_description', '')}".strip()
        except ValueError:
            detail = r.text[:120]
        raise AuthError(f"login rechazado ({r.status_code}): {detail}")
    data = r.json()
    email = _decode_jwt(data["access_token"]).get("email", "")
    return Session(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        user_id=derive_user_id(email),
        expires_in=int(data.get("expires_in", 0)),
        refresh_expires_in=int(data.get("refresh_expires_in", 0)),
    )


def login(username: str, password: str) -> Session:
    """Un solo intento ROPC; el caller decide reintentos (jamás en loop aquí:
    reintentos agresivos con creds reales pueden bloquear la cuenta)."""
    return _post({
        "grant_type": "password",
        "client_id": SSO_CLIENT_ID,
        "scope": SCOPE,
        "username": username,
        "password": password,
    })


def refresh(refresh_token: str) -> Session:
    """Renueva la sesión con el refresh token (~25h de validez), sin pedir
    la contraseña de nuevo."""
    return _post({
        "grant_type": "refresh_token",
        "client_id": SSO_CLIENT_ID,
        "refresh_token": refresh_token,
    })
