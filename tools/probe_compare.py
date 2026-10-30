#!/usr/bin/env python3
"""Compara los claims del token de la sesion web (DevTools) contra los del ROPC.

El token de sesion NUNCA se imprime: solo el diff de claims, que no es una credencial.

    $env:UTP_BROWSER_TOKEN = "<valor del header authorization de DevTools, sin Bearer>"
    .venv\\Scripts\\python.exe tools\\probe_compare.py
"""

import base64
import json
import os
import sys

import requests

SSO_TOKEN = "https://sso.utp.edu.pe/auth/realms/Xpedition/protocol/openid-connect/token"


def decode(tok: str) -> dict:
    raw = tok.split(".")[1].replace("-", "+").replace("_", "/")
    raw += "=" * ((4 - len(raw) % 4) % 4)
    out = json.loads(base64.b64decode(raw))
    out.pop("exp", None)   # siempre difieren por tiempos; ruido
    out.pop("iat", None)
    out.pop("jti", None)
    return out


def main() -> int:
    browser = os.environ.get("UTP_BROWSER_TOKEN", "").replace("Bearer ", "").strip()

    r = requests.post(
        SSO_TOKEN,
        data={"grant_type": "password", "client_id": "pao-web",
              "username": os.environ.get("UTP_USER", ""),
              "password": os.environ.get("UTP_PASS", "")},
        timeout=30,
    )
    ropc = decode(r.json()["access_token"]) if r.status_code == 200 else {}
    print("ROPC ok" if ropc else f"ROPC fallo: {r.status_code}")

    if not browser:
        print("Falta UTP_BROWSER_TOKEN (header authorization de la sesion web)")
        return 2

    web = decode(browser)
    all_keys = sorted(set(web) | set(ropc), key=str.lower)
    print("\nDIFF DE CLAIMS (web vs ropc):\n")
    for k in all_keys:
        w, o = web.get(k, "<ausente>"), ropc.get(k, "<ausente>")
        if json.dumps(w, sort_keys=True) != json.dumps(o, sort_keys=True):
            print(f"  {k}:\n    web : {w}\n    ropc: {o}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")
    try:
        sys.exit(main())
    except Exception as e:
        print(f"error: {e}")
        sys.exit(1)
