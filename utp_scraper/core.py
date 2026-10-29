# utp_scraper.core — orquestación extraída de utp_scraper_v2.2.py (líneas 235-288)
# El núcleo NO depende de rich: notifica por eventos (contrato INFORME §4).

import os
import time

from utp_scraper.downloader import download_file, extract_urls_from_html, sanitize

# Formatos a descargar; mp3 excluido por defecto (el audio ya viene en el mp4).
DOWNLOAD_EXTENSIONS = {"pdf", "mp4", "docx", "xlsx", "pptx", "png", "jpg", "jpeg"}


def collect_jobs(data: dict, course_name: str) -> list:
    """Mapea data['unities'] → jobs (week_label, title, theme_folder_rel, url, ext).

    theme_folder_rel es relativo a la raíz de descarga; run_jobs le añade root.
    """
    jobs = []
    course_folder = sanitize(course_name)
    for unity in data.get("unities", []):
        for theme in unity.get("themes", []):
            week = theme.get("weekNumber")
            week_label = f"Semana_{week:02d}" if isinstance(week, int) else "Semana_00"
            theme_name = sanitize(theme.get("name", "tema"))
            theme_folder = os.path.join(course_folder, week_label, theme_name)

            for content in theme.get("contents", []):
                ctype = content.get("type")
                title = content.get("title") or content.get("contentId")
                metadata = content.get("metadata", {}) or {}

                urls = []
                if ctype == "FILE" and metadata.get("url"):
                    ext = metadata.get("filetype", "").lower() or "bin"
                    urls = [(metadata["url"], ext)]
                elif ctype == "HTML" and metadata.get("contentHtml"):
                    urls = extract_urls_from_html(metadata["contentHtml"])
                elif ctype in ("HOMEWORK", "EVALUATION"):
                    urls = extract_urls_from_html(content.get("description") or "")

                for url, ext in urls:
                    jobs.append((week_label, title, theme_folder, url, ext))
    return jobs


def run_jobs(jobs, root_dir: str, on_event) -> dict:
    """Ejecuta jobs llamando on_event(nombre_evento, **kwargs) y devolviendo conteos.

    Returns: {"ok": n, "skip_exist": n, "error": n, "filtered_format": n}
    """
    counts = {"ok": 0, "skip_exist": 0, "error": 0, "filtered_format": 0}
    for week_label, title, theme_folder, url, ext in jobs:
        if ext.lower() not in DOWNLOAD_EXTENSIONS:
            counts["filtered_format"] += 1
            on_event("filtered_format", week=week_label, title=title, ext=ext)
            continue
        dest_folder = os.path.join(root_dir, theme_folder)
        result, filename = download_file(url, ext, dest_folder, sanitize(title))
        if result == "ok":
            counts["ok"] += 1
            on_event("downloaded", week=week_label, title=title, filename=filename)
        elif result == "skip_exist":
            counts["skip_exist"] += 1
            on_event("skipped_existing", week=week_label, title=title, filename=filename)
        else:
            counts["error"] += 1
            on_event("error", week=week_label, title=title, filename=filename, detail=result)
        # Pausa anti-throttle del S3; documentada, no eliminar.
        time.sleep(0.1)
    return counts
