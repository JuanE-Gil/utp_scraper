#!/usr/bin/env python3
"""
Sonda Fase 1 — UTP+class Downloader v3
======================================
Resuelve las incógnitas de la Fase 1 sin escribir valores sensibles a disco:

  1. ¿Qué endpoint devuelve `academicPeriods`?            (INFORME §11.3)
  2. ¿Qué campo identifica la sección y sirve en /full?   (ADR-0005)
  3. ¿Basta `requests` + academicPeriodId, o hace falta fetch en el navegador?
  4. ¿Una consulta a un período anterior devuelve cursos?  (B5)
  5. Vida útil del token (segundos, sin mostrar el token).

Garantías:
  - La contraseña se pide con getpass, se usa una vez y se descarta (ADR-0001).
  - Token, user-id y tenant-id viven solo en memoria.
  - El reporte contiene NOMBRES de campos, tipos, códigos HTTP y URLs con los
    UUID reemplazados por <uuid>. Nunca valores de datos personales.
  - Si el login falla, aborta. No reintenta (ADR-0001).
  - Solo consulta datos que provienen de la matrícula del propio usuario (ADR-0002).

Uso:  python tools/probe_fase1.py
Salida: fase1_reporte.json (añádelo a .gitignore por prudencia).
"""

import base64
import getpass
import json
import re
import sys
from datetime import datetime

import requests
from playwright.sync_api import sync_playwright

LOGIN_URL = (
    "https://sso.utp.edu.pe/auth/realms/Xpedition/protocol/openid-connect/auth"
    "?client_id=pao-web&redirect_uri=https%3A%2F%2Fclass.utp.edu.pe%2Fstudent%2Fcourses"
    "&state=b408bd68-fbbc-45ea-a1e3-c96428b204e5&response_mode=fragment"
    "&response_type=code&scope=openid&nonce=4de8c449-307a-4624-8556-1f6c58de61d5"
)
API_HOST = "api-pao.utpxpedition.com"
COURSES_URL = f"https://{API_HOST}/course/student/courses"
REPORT_PATH = "fase1_reporte.json"

UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
# Únicos campos cuyo VALOR se registra (son enumeraciones, no datos personales).
SAFE_VALUE_KEYS = {"type", "period"}
SECTION_CANDIDATES = ["sectionId", "sectionCode", "section"]
COURSE_CANDIDATES = ["courseId", "id"]


# ---------- utilidades de redacción ----------
def redact_url(url: str) -> str:
    return UUID_RE.sub("<uuid>", url)


def shape(obj, depth=0, max_depth=6):
    """Estructura (claves y tipos) sin valores, salvo enumeraciones seguras."""
    if depth > max_depth:
        return "..."
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in SAFE_VALUE_KEYS and isinstance(v, (str, int)) and len(str(v)) < 40:
                out[k] = f"{type(v).__name__} = {v!r}"
            else:
                out[k] = shape(v, depth + 1, max_depth)
        return out
    if isinstance(obj, list):
        if not obj:
            return {"_list_len": 0}
        return {"_list_len": len(obj), "_item": shape(obj[0], depth + 1, max_depth)}
    return type(obj).__name__


def looks_like_uuid(v) -> bool:
    return isinstance(v, str) and bool(UUID_RE.fullmatch(v))


def find_key(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find_key(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_key(v, key)
            if r is not None:
                return r
    return None


def jwt_lifetime_seconds(token: str):
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return int(data["exp"]) - int(data["iat"])
    except Exception:
        return None


# ---------- sondas HTTP ----------
def build_headers(creds: dict) -> dict:
    return {
        "accept": "*/*",
        "authorization": creds["authorization"],
        "origin": "https://class.utp.edu.pe",
        "referer": "https://class.utp.edu.pe/",
        "transaction-id": "00000000-0000-0000-0000-000000000000",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "user-id": creds["user-id"],
        "user-role": "STUDENT",
        "x-tenant-id": creds["x-tenant-id"],
    }


def probe_requests(headers: dict, url: str):
    entry = {"via": "requests", "url": redact_url(url)}
    body = None
    try:
        r = requests.get(url, headers=headers, timeout=20)
        entry["status"] = r.status_code
        if "json" in r.headers.get("content-type", ""):
            body = r.json()
            entry["shape"] = shape(body)
    except Exception as e:
        entry["error"] = type(e).__name__
    return entry, body


def probe_browser_fetch(page, url: str):
    entry = {"via": "browser_fetch", "url": redact_url(url)}
    try:
        res = page.evaluate(
            """async (u) => {
                try {
                    const r = await fetch(u);
                    let b = null;
                    try { b = await r.json(); } catch (e) {}
                    return {status: r.status, body: b};
                } catch (e) { return {status: null, body: null}; }
            }""",
            url,
        )
        entry["status"] = res["status"]
        if res["body"] is not None:
            entry["shape"] = shape(res["body"])
    except Exception as e:
        entry["error"] = type(e).__name__
    return entry


def section_field_matrix(courses: list) -> dict:
    """Por campo candidato: cuántos cursos lo traen, no vacío, y cuántos parecen UUID."""
    matrix = {}
    for field in SECTION_CANDIDATES + COURSE_CANDIDATES:
        present = [c.get(field) for c in courses if isinstance(c, dict) and field in c]
        non_empty = [v for v in present if v not in (None, "", [])]
        matrix[field] = {
            "present_in": len(present),
            "non_empty": len(non_empty),
            "uuid_like": sum(looks_like_uuid(v) for v in non_empty),
            "types": sorted({type(v).__name__ for v in non_empty}),
        }
    return matrix


def probe_section_full(headers: dict, course: dict) -> list:
    """Prueba combinaciones (campo de curso, campo de sección) SOLO con valores
    del primer curso de la matrícula propia. Se detiene en el primer 200."""
    results = []
    for cf in COURSE_CANDIDATES:
        for sf in SECTION_CANDIDATES:
            cid, sid = course.get(cf), course.get(sf)
            if not (isinstance(cid, str) and isinstance(sid, str) and cid and sid):
                continue
            url = f"{COURSES_URL}/{cid}/sections/{sid}/full"
            entry, body = probe_requests(headers, url)
            entry["combo"] = f"course={cf}, section={sf}"
            if isinstance(body, dict) and isinstance(body.get("data"), dict):
                entry["data_keys"] = sorted(body["data"].keys())
            results.append(entry)
            if entry.get("status") == 200:
                return results
    return results


# ---------- flujo principal ----------
def main():
    print("Sonda Fase 1 — no se guardan credenciales ni valores de datos.\n")
    codigo = input("Código institucional: ").strip()
    contrasena = getpass.getpass("Contraseña: ")

    report = {"generated_at": datetime.now().isoformat(timespec="seconds"), "endpoints_seen": []}
    creds, bodies = {}, []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_context().new_page()

        def on_response(resp):
            if API_HOST not in resp.url:
                return
            req = resp.request
            h = req.headers
            if "authorization" in h and "user-id" in h:
                creds["authorization"] = h["authorization"]
                creds["user-id"] = h["user-id"]
                creds["x-tenant-id"] = h.get("x-tenant-id", "")
            entry = {"method": req.method, "url": redact_url(resp.url), "status": resp.status}
            try:
                if "json" in resp.headers.get("content-type", ""):
                    body = resp.json()
                    entry["shape"] = shape(body)
                    bodies.append((redact_url(resp.url), body))
            except Exception:
                pass
            report["endpoints_seen"].append(entry)

        page.on("response", on_response)

        try:
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("input[type='text'], input[type='email'], #username", timeout=15000)
            page.fill("input[type='text'], input[type='email'], #username", codigo)
            page.click("input[type='submit'], button[type='submit']")
            page.wait_for_selector("input[type='password']", timeout=15000)
            page.fill("input[type='password']", contrasena)
            contrasena = None  # descartada
            page.click("input[type='submit'], button[type='submit']")
            try:
                page.wait_for_selector("input[id='idSIButton9']", timeout=4000)
                page.click("input[id='idSIButton9']")
            except Exception:
                pass
            page.wait_for_selector("text=Actividades semanales", timeout=25000)
            page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Login no completado ({type(e).__name__}). Se aborta sin reintentar (ADR-0001).")
            browser.close()
            sys.exit(1)
        finally:
            contrasena = None

        if not creds.get("authorization"):
            print("No se capturaron headers de autorización. Abortando.")
            browser.close()
            sys.exit(1)

        raw = creds["authorization"]
        token = raw[7:] if raw.startswith("Bearer ") else raw
        report["token_lifetime_seconds"] = jwt_lifetime_seconds(token)
        report["tenant_header_present"] = bool(creds.get("x-tenant-id"))

        # 1) Endpoint de períodos
        periods, periods_url = None, None
        for url, body in bodies:
            found = find_key(body, "academicPeriods")
            if isinstance(found, list):
                periods, periods_url = found, url
                break
        report["periods_endpoint"] = periods_url
        if not periods:
            report["periods_found"] = False
            print("No se encontró 'academicPeriods' en el tráfico capturado.")
            browser.close()
            _save(report)
            return

        report["periods_found"] = True
        report["periods_summary"] = {
            "count": len(periods),
            "type_values": sorted({str(x.get("type")) for x in periods if isinstance(x, dict)}),
            "item_keys": sorted(periods[0].keys()) if isinstance(periods[0], dict) else None,
        }
        current = next(
            (x for x in periods if x.get("type") == "CURRENT_PERIOD" and x.get("period") != "9999"), None
        )
        previous = next(
            (x for x in periods if x is not current and x.get("id") and x.get("type") != "CURRENT_PERIOD"), None
        )
        report["current_period_found"] = current is not None
        report["previous_period_available"] = previous is not None

        headers = build_headers(creds)
        probes = []

        # 2) Cursos: baseline sin parámetro (reproduce el 500 documentado)
        e, _ = probe_requests(headers, COURSES_URL)
        e["label"] = "baseline_sin_periodo"
        probes.append(e)

        courses_body = None
        if current:
            url = f"{COURSES_URL}?academicPeriodId={current['id']}"
            e, courses_body = probe_requests(headers, url)
            e["label"] = "requests_periodo_vigente"
            probes.append(e)
            f = probe_browser_fetch(page, url)
            f["label"] = "browser_fetch_periodo_vigente"
            probes.append(f)

        # 3) Período anterior (B5)
        if previous:
            url = f"{COURSES_URL}?academicPeriodId={previous['id']}"
            e, prev_body = probe_requests(headers, url)
            e["label"] = "requests_periodo_anterior"
            if isinstance(prev_body, dict) and isinstance(prev_body.get("data"), list):
                e["courses_count"] = len(prev_body["data"])
            probes.append(e)

        # 4) Campo de sección (ADR-0005) y validez en /full
        courses = courses_body.get("data") if isinstance(courses_body, dict) else None
        if isinstance(courses, list) and courses:
            report["courses_count_current"] = len(courses)
            report["section_field_matrix"] = section_field_matrix(courses)
            if isinstance(courses[0], dict):
                report["course_item_keys"] = sorted(courses[0].keys())
                report["section_full_probe"] = probe_section_full(headers, courses[0])
        report["probes"] = probes

        browser.close()

    # Conclusiones automáticas (hipótesis a confirmar leyendo el reporte)
    ok_req = any(x.get("label") == "requests_periodo_vigente" and x.get("status") == 200 for x in probes)
    report["conclusions"] = {
        "requests_suficiente_con_periodo": ok_req,
        "baseline_reproduce_500": any(
            x.get("label") == "baseline_sin_periodo" and x.get("status") == 500 for x in probes
        ),
    }
    _save(report)


def _save(report: dict):
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReporte guardado en {REPORT_PATH} (sin credenciales ni valores de datos).")
    print(json.dumps(report.get("conclusions", {}), indent=2))


if __name__ == "__main__":
    main()