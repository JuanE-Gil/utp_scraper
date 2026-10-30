#!/usr/bin/env python3
"""
Sonda Fase 1b — UTP+class Downloader v3
=======================================
Responde tres preguntas abiertas tras el hallazgo de `dashboard-courses`:

  1. ¿`requests` (sin navegador) basta para dashboard-courses y academicperiods?
  2. ¿Los items de academicperiods se enlazan con los cursos por la tupla
     (period, acadCareer, module)?
  3. ¿El contenido (/full) de períodos anteriores sigue accesible? (riesgo de B5)

Garantías (igual que la sonda 1):
  - Contraseña por getpass, usada una vez; si el login falla, aborta sin reintentar (ADR-0001).
  - Token e IDs solo en memoria; el navegador se cierra justo después del login.
  - Solo GET de lectura sobre la matrícula del propio usuario (ADR-0002).
  - El reporte contiene conteos, códigos HTTP y nombres de campo. No nombres de
    cursos, docentes, IDs ni correos.

Uso:  python tools/probe_fase1b.py      Salida: fase1b_reporte.json
"""

import getpass
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime

import requests
from playwright.sync_api import sync_playwright

LOGIN_URL = (
    "https://sso.utp.edu.pe/auth/realms/Xpedition/protocol/openid-connect/auth"
    "?client_id=pao-web&redirect_uri=https%3A%2F%2Fclass.utp.edu.pe%2Fstudent%2Fcourses"
    "&state=b408bd68-fbbc-45ea-a1e3-c96428b204e5&response_mode=fragment"
    "&response_type=code&scope=openid&nonce=4de8c449-307a-4624-8556-1f6c58de61d5"
)
API = "https://api-pao.utpxpedition.com"
REPORT_PATH = "fase1b_reporte.json"


def login_and_capture_headers(codigo: str, contrasena: str) -> dict:
    creds = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_context().new_page()

        def on_response(resp):
            if "api-pao.utpxpedition.com" not in resp.url:
                return
            h = resp.request.headers
            if "authorization" in h and "user-id" in h:
                creds["authorization"] = h["authorization"]
                creds["user-id"] = h["user-id"]
                creds["x-tenant-id"] = h.get("x-tenant-id", "")

        page.on("response", on_response)
        try:
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("input[type='text'], input[type='email'], #username", timeout=15000)
            page.fill("input[type='text'], input[type='email'], #username", codigo)
            page.click("input[type='submit'], button[type='submit']")
            page.wait_for_selector("input[type='password']", timeout=15000)
            page.fill("input[type='password']", contrasena)
            page.click("input[type='submit'], button[type='submit']")
            try:
                page.wait_for_selector("input[id='idSIButton9']", timeout=4000)
                page.click("input[id='idSIButton9']")
            except Exception:
                pass
            page.wait_for_selector("text=Actividades semanales", timeout=25000)
            page.wait_for_timeout(4000)
        except Exception as e:
            print(f"Login no completado ({type(e).__name__}). Se aborta sin reintentar (ADR-0001).")
            browser.close()
            sys.exit(1)
        browser.close()
    if not creds.get("authorization"):
        print("No se capturaron headers de autorización. Abortando.")
        sys.exit(1)
    return creds


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


def get_json(url: str, headers: dict):
    """Devuelve (status, data|None). Nunca lanza."""
    try:
        r = requests.get(url, headers=headers, timeout=30)
        body = r.json() if "json" in r.headers.get("content-type", "") else None
        return r.status_code, (body.get("data") if isinstance(body, dict) else None)
    except Exception as e:
        return type(e).__name__, None


def tuple_of(item: dict):
    return (item.get("period"), item.get("acadCareer"), item.get("module"))


def count_full(data) -> dict:
    unities = (data or {}).get("unities") or []
    themes = [t for u in unities for t in (u.get("themes") or [])]
    contents = [c for t in themes for c in (t.get("contents") or [])]
    return {"unities": len(unities), "themes": len(themes), "contents": len(contents)}


def main():
    print("Sonda Fase 1b — no se guardan credenciales ni datos personales.\n")
    codigo = input("Código institucional: ").strip()
    contrasena = getpass.getpass("Contraseña: ")
    creds = login_and_capture_headers(codigo, contrasena)
    contrasena = None  # descartada; el navegador ya está cerrado

    headers = build_headers(creds)
    user_id = creds["user-id"]
    report = {"generated_at": datetime.now().isoformat(timespec="seconds")}

    # 1) dashboard-courses con requests puro
    st, courses = get_json(f"{API}/learning/student/{user_id}/dashboard-courses", headers)
    report["dashboard_courses"] = {"via": "requests", "status": st}
    if not isinstance(courses, list):
        report["dashboard_courses"]["note"] = "sin lista; no se continúa"
        _save(report)
        return

    by_period = Counter(c.get("period") for c in courses)
    tuples = Counter(tuple_of(c) for c in courses)
    course_ids = Counter(c.get("courseId") for c in courses)
    name_in_period = Counter((c.get("period"), c.get("name")) for c in courses)
    report["dashboard_courses"].update(
        {
            "total": len(courses),
            "item_keys": sorted(courses[0].keys()),
            "courses_per_period": dict(by_period),
            "distinct_period_acad_module": len(tuples),
            "section_id_is_uuid_like": all(
                isinstance(c.get("sectionId"), str) and len(c["sectionId"]) == 36 for c in courses
            ),
            "section_ids_unique": len({c.get("sectionId") for c in courses}) == len(courses),
            "courseIds_repeated_across_sections": sum(1 for n in course_ids.values() if n > 1),
            "same_name_twice_in_same_period": sum(1 for n in name_in_period.values() if n > 1),
        }
    )

    # 2) academicperiods con requests puro + join por tupla
    st, periods = get_json(f"{API}/course/student/{user_id}/academicperiods", headers)
    report["academic_periods"] = {"via": "requests", "status": st}
    if isinstance(periods, dict):
        periods = periods.get("academicPeriods")
    if isinstance(periods, list):
        ptuples = Counter(tuple_of(x) for x in periods)
        report["academic_periods"].update(
            {
                "count": len(periods),
                "types": dict(Counter(x.get("type") for x in periods)),
                "table": [
                    {
                        "period": x.get("period"),
                        "acadCareer": x.get("acadCareer"),
                        "module": x.get("module"),
                        "type": x.get("type"),
                        "active": x.get("active"),
                        "name": x.get("name"),
                    }
                    for x in periods
                ],
                "tuples_unique_in_periods": all(n == 1 for n in ptuples.values()),
                "join_matched": sum(1 for t in tuples if t in ptuples),
                "join_total": len(tuples),
                "periods_without_courses": sum(1 for t in ptuples if t not in tuples),
            }
        )

    # 3) /full de UNA sección por período (propia matrícula, solo lectura)
    first_by_period = {}
    for c in courses:
        first_by_period.setdefault(c.get("period"), c)
    full_results = []
    for period, c in first_by_period.items():
        url = f"{API}/course/student/courses/{c['courseId']}/sections/{c['sectionId']}/full"
        st, data = get_json(url, headers)
        entry = {"period": period, "status": st}
        if isinstance(data, dict):
            entry.update(count_full(data))
        full_results.append(entry)
        time.sleep(0.3)
    report["full_per_period"] = full_results

    ok_all = all(x["status"] == 200 for x in full_results)
    report["conclusions"] = {
        "requests_basta_para_listado": report["dashboard_courses"]["status"] == 200,
        "periodos_anteriores_accesibles_en_full": ok_all,
        "join_por_tupla_completo": report.get("academic_periods", {}).get("join_matched")
        == report.get("academic_periods", {}).get("join_total"),
    }
    _save(report)


def _save(report: dict):
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReporte guardado en {REPORT_PATH}")
    print(json.dumps(report.get("conclusions", {}), indent=2))


if __name__ == "__main__":
    main()