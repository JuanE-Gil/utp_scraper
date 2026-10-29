# utp_scraper.api — llamadas HTTP puras a la API (capa api, INFORME §4)
# Port verbatim de los headers de utp_scraper_v2.2.py:65-77 y get_section_full de :123-127.

import requests

API_BASE = "https://api-pao.utpxpedition.com/course/student/courses"


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
