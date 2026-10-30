# utp_scraper.core — orquestación extraída de utp_scraper_v2.2.py (líneas 235-288)
# El núcleo NO depende de rich: notifica por eventos (contrato INFORME §4).

import os
import time

from utp_scraper.downloader import download_file, extract_urls_from_html, sanitize

# Formatos a descargar; mp3 excluido por defecto (el audio ya viene en el mp4).
DOWNLOAD_EXTENSIONS = {"pdf", "mp4", "docx", "xlsx", "pptx", "png", "jpg", "jpeg"}


def collect_jobs(data: dict, course_name: str, folder: str = None) -> list:
    """Mapea data['unities'] → jobs (week_label, title, theme_folder_rel, url, ext).

    theme_folder_rel es relativo a la raíz de descarga; run_jobs le añade root.
    `folder` (opcional) es la carpeta relativa del curso ya resuelta (p. ej. la de
    group_courses_by_period); sin ella se usa sanitize(course_name) como antes.
    """
    jobs = []
    course_folder = folder if folder else sanitize(course_name)
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


# ---------------------------------------------------------------------------
# Matrícula agrupada por ciclo (Épica B). Lógica pura: sin red, sin UI.
# Entrada: items de api.list_dashboard_courses y (opcional) api.list_academic_periods.
# ---------------------------------------------------------------------------
DEFAULT_PERIOD = "9999"  # pseudo-período (cursos transversales); nunca es "el ciclo vigente"


def _is_valid_course(c) -> bool:
    # ADR-0005: la identidad de la sección es `sectionId`; sin alias de respaldo.
    return (
        isinstance(c, dict)
        and isinstance(c.get("sectionId"), str) and bool(c["sectionId"])
        and isinstance(c.get("courseId"), str) and bool(c["courseId"])
    )


def _code_num(period) -> int:
    return int(period) if isinstance(period, str) and period.isdigit() else 0


def group_courses_by_period(courses: list, periods: list = None):
    """Agrupa la matrícula por (period, acadCareer, module).

    La tupla, y no `period` solo, es la clave: el período 9999 contiene dos módulos
    distintos (verificado en la Fase 1; las 6 tuplas coinciden 1:1 con academicperiods).

    Devuelve (grupos, excluidos). Cada grupo: key, label, is_current, is_default,
    folder (relativa, única) y courses (registros normalizados, sin datos de docentes).
    Orden: vigente, ciclos anteriores por código descendente, pseudo-período al final.
    Excluidos: items sin sectionId/courseId válidos (matriz §8); se avisan, no se ofrecen.

    Sin `periods` (llamada fallida) la etiqueta cae a "Ciclo <código>" y se marca como
    vigente el mayor código regular: heurística de respaldo, no un hecho verificado.
    """
    valid = [c for c in courses if _is_valid_course(c)]
    excluded = [c for c in courses if not _is_valid_course(c)]

    meta = {}
    for p in periods or []:
        if isinstance(p, dict):
            meta[(p.get("period"), p.get("acadCareer"), p.get("module"))] = p

    buckets = {}
    for c in valid:
        buckets.setdefault((c.get("period"), c.get("acadCareer"), c.get("module")), []).append(c)

    groups = []
    for key, items in buckets.items():
        period, career, module = key
        m = meta.get(key)
        label = (m.get("name") if m and m.get("name") else None) or (
            f"Ciclo {period} ({module})" if module else f"Ciclo {period}"
        )
        is_default = period == DEFAULT_PERIOD
        is_current = bool(m and m.get("type") == "CURRENT_PERIOD" and not is_default)
        groups.append({"key": key, "label": label, "is_current": is_current,
                       "is_default": is_default, "courses": items})

    if not meta:
        regular = [g for g in groups if not g["is_default"]]
        if regular:
            max(regular, key=lambda g: _code_num(g["key"][0]))["is_current"] = True

    groups.sort(key=lambda g: (
        0 if g["is_current"] else (2 if g["is_default"] else 1),
        -_code_num(g["key"][0]),
        str(g["key"][2]),
    ))

    used_group_folders = set()
    for g in groups:
        base = sanitize(g["label"])
        if base in used_group_folders:
            base = sanitize(f"{g['label']} {g['key'][0]}-{g['key'][2]}")
        used_group_folders.add(base)
        g["folder"] = base

        # Ante homónimos dentro del ciclo, TODOS llevan sufijo: así la carpeta no depende
        # del orden en que la API devuelva la lista (rompería la idempotencia).
        base_names = [sanitize(c.get("name") or "sin nombre") for c in g["courses"]]
        counts = {n: base_names.count(n) for n in base_names}
        records = []
        for c, name in zip(g["courses"], base_names):
            if counts[name] > 1:
                suffix = c.get("classNumber") or c["sectionId"][:8]
                name = sanitize(f"{name} ({suffix})")
            records.append({
                "section_id": c["sectionId"],
                "course_id": c["courseId"],
                "name": c.get("name") or "Sin nombre",
                "class_number": c.get("classNumber"),
                "modality": c.get("modality"),
                "period": c.get("period"),
                "folder": os.path.join(base, name),
            })
        g["courses"] = records

    return groups, excluded