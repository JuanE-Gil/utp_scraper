#!/usr/bin/env python3
"""Probe: login via ROPC (sin navegador) + llamada read-only a dashboard-courses.

Credenciales SOLO por variables de entorno (regla del repo):
    UTP_USER, UTP_PASS           -> para el password grant de Keycloak
    UTP_USER_ID, UTP_TENANT_ID   -> valores capturados del navegador (DevTools F12)

Imprime solo estados y conteos; nunca el token, ni el password, ni los IDs completos.
Un solo login; maximo 2 llamadas read-only con el mismo token.
"""

import base64
import json
import os
import sys

import requests

SSO_TOKEN = "https://sso.utp.edu.pe/auth/realms/Xpedition/protocol/openid-connect/token"
API = "https://api-pao.utpxpedition.com"
SCOPE = "openid roles-client-pao-web profile email roles-realm-xpedition"


def jwt_payload(token: str) -> dict:
    raw = token.split(".")[1].replace("-", "+").replace("_", "/")
    raw += "=" * ((4 - len(raw) % 4) % 4)
    return json.loads(base64.b64decode(raw))


def main() -> int:
    user, password = os.environ.get("UTP_USER"), os.environ.get("UTP_PASS")
    if not user or not password:
        print("USO: set UTP_USER/UTP_PASS (y opcionalmente UTP_USER_ID/UTP_TENANT_ID)")
        return 2

    # 1) password grant (un solo intento, sin loops)
    r = requests.post(
        SSO_TOKEN,
        data={"grant_type": "password", "client_id": "pao-web",
              "username": user, "password": password, "scope": SCOPE},
        timeout=30,
    )
    if r.status_code != 200:
        print(f"ROPC: {r.status_code} {r.json().get('error', '?')}")
        return 1
    tok = r.json()
    refresh_hours = tok.get("refresh_expires_in", 0) / 3600
    print(f"ROPC: OK (access 24h, refresh ~{refresh_hours:.1f}h, sin navegador)")

    sub = jwt_payload(tok["access_token"]).get("sub", "?")

    # 2) dashboard-courses con el mismo token (read-only)
    user_id = os.environ.get("UTP_USER_ID", sub)
    tenant = os.environ.get("UTP_TENANT_ID", "")
    headers = {
        "accept": "*/*",
        # El gateway exige el prefijo Bearer: sin el, responde 403 (verificado).
        "authorization": f"Bearer {tok['access_token']}",
        "origin": "https://class.utp.edu.pe",
        "referer": "https://class.utp.edu.pe/",
        "transaction-id": "00000000-0000-0000-0000-000000000000",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "user-id": user_id,
        "user-role": "STUDENT",
        "x-tenant-id": tenant,
    }
    r2 = requests.get(f"{API}/learning/student/{user_id}/dashboard-courses",
                      headers=headers, timeout=30)
    print(f"API: {r2.status_code}")
    if r2.status_code == 200:
        data = r2.json().get("data", [])
        print(f"CURSOS: {len(data)}")
        if data:
            c = data[0]
            print(f"PRIMERA_TUPLA: {c.get('period')} {c.get('acadCareer')} {c.get('module')}")
    else:
        print(f"CUERPO: {r2.text[:200]}")
    return 0 if r2.status_code == 200 else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
    try:
        sys.exit(main())
    except Exception as e:  # nunca crash con traceback crudo
        print(f"error: {e}")
        sys.exit(1)
