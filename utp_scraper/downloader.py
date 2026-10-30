# utp_scraper.downloader — lógica pura extraída verbatim de utp_scraper_v2.2.py (líneas 83-163)
# Extracto de URLs del S3 académico y descarga con idempotencia por tamaño > 0.

import os
import re
import unicodedata
from typing import Tuple
from urllib.parse import unquote, urlparse

import requests

UTP_FILE_DOMAIN = "utp-prd-upload-file-storage.s3.amazonaws.com"
FILE_EXT_RE = re.compile(
    r"https?://" + re.escape(UTP_FILE_DOMAIN) + r"/[^\s\"'<>]+?\.(pdf|mp4|mp3|docx?|xlsx?|pptx?|png|jpe?g)",
    re.IGNORECASE,
)


def sanitize(name: str, max_len: int = 120) -> str:
    name = unquote(name)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", " ", name).strip(" ._")
    return name[:max_len] if name else "sin_nombre"


def extract_urls_from_html(html: str) -> list:
    """Devuelve lista de (url, ext) únicos preservando orden, solo del S3 académico."""
    if not html:
        return []
    seen = set()
    out = []
    for m in FILE_EXT_RE.finditer(html):
        url = m.group(0)
        ext = m.group(1).lower()
        if url not in seen:
            seen.add(url)
            out.append((url, ext))
    return out


def download_file(url: str, ext: str, dest_folder: str, fallback_name: str) -> Tuple[str, str]:
    """Devuelve ('ok' | 'skip_exist' | 'error: causa', nombre_destino)."""
    os.makedirs(dest_folder, exist_ok=True)
    parsed_name = sanitize(os.path.basename(urlparse(url).path)) or f"{fallback_name}.{ext}"
    dest_path = os.path.join(dest_folder, parsed_name)

    # Un archivo de tamaño 0 es una descarga previa corrupta: se re-descarga.
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return "skip_exist", parsed_name

    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
        return "ok", parsed_name
    except Exception as e:
        # Un corte a mitad de stream NO deja un parcial >0 como válido: se elimina.
        try:
            if os.path.exists(dest_path):
                os.remove(dest_path)
        except OSError:
            pass
        return f"error: {e}", parsed_name