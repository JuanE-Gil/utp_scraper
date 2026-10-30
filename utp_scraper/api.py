# utp_scraper.api — llamadas HTTP puras a la API (capa api, INFORME §4)
# Port verbatim de los headers de utp_scraper_v2.2.py:65-77 y get_section_full de :123-127.

import requests

API_ROOT = "https://api-pao.utpxpedition.com"
API_BASE = f"{API_ROOT}/course/student/courses"


def build_headers(auth_token: str, user_id: str, tenant_id: str) -> dict:
    return {
        "accept": "*/*",
        "authorization": f"Bearer {auth_token}",
        "origin": "https://class.utp.edu.pe",
        "referer": "https://class.utp.edu.pe/",
        "transaction-id": "00000000-0000-0000-0000-000000000000",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "user-id": user_id,
        "user-role": "STUDENT",
        "x-tenant-id": tenant_id,
    }


def get_section_full(course_id: str, section_id: str, headers: dict) -> dict:
    url = f"{API_BASE}/{course_id}/sections/{section_id}/full"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["data"]


def list_dashboard_courses(user_id: str, headers: dict) -> list:
    """Matrícula completa del usuario, de TODOS los ciclos, en una sola llamada.

    Fuente única de la lista de cursos (ADR-0002: nunca se ofrecen secciones fuera
    de esta respuesta). Verificado en la Fase 1 con `requests` puro; cada item trae
    `sectionId` (UUID) y `courseId`. `/course/student/courses` NO es el endpoint
    correcto: respondió 500 con y sin `academicPeriodId`.
    """
    url = f"{API_ROOT}/learning/student/{user_id}/dashboard-courses"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["data"]


def list_academic_periods(user_id: str, headers: dict) -> list:
    """Períodos académicos del usuario. Solo aporta etiquetas legibles y cuál es el
    vigente (type == CURRENT_PERIOD y period != "9999"); no filtra cursos."""
    url = f"{API_ROOT}/course/student/{user_id}/academicperiods"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["data"]["academicPeriods"]