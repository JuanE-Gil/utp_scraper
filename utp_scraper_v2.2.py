#!/usr/bin/env python3
"""
UTP+class Material Downloader â€” versiÃ³n visual (TUI)
=======================================================
Descarga todos los materiales de tus cursos en UTP+class con una interfaz
visual en la terminal (tipo lazygit/lazydocker), organizados por
curso / semana / tema.

INSTALACIÃ“N:
    pip install requests rich --break-system-packages

CÃ“MO OBTENER LOS DATOS QUE NECESITAS RELLENAR ABAJO:

1. AUTH_TOKEN, USER_ID, TENANT_ID:
   - Abre class.utp.edu.pe y entra a cualquier curso.
   - F12 -> pestaÃ±a Network -> filtra "Fetch/XHR".
   - Click en cualquier request hacia "api-pao.utpxpedition.com".
   - En "Headers" copia:
       authorization: Bearer XXXXX   -> pega solo la parte XXXXX en AUTH_TOKEN
       user-id: XXXXX                -> USER_ID
       x-tenant-id: XXXXX            -> TENANT_ID

2. COURSES (lista de cursos a descargar):
   - Ve a "Mis cursos", entra a cada curso, y mira la URL:
     class.utp.edu.pe/student/courses/{COURSE_ID}/section/{SECTION_ID}/...
   - Copia esos dos IDs por cada curso en la lista COURSES de abajo.

NOTA DE SEGURIDAD: el AUTH_TOKEN es tu sesiÃ³n personal. No lo compartas
con nadie ni lo subas a repositorios pÃºblicos. Expira en ~24h.
"""

import os
import re
import time
import unicodedata
import requests
from dataclasses import dataclass, field
from urllib.parse import unquote, urlparse

from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.console import Console, Group
from rich.text import Text

# ============ CONFIGURA ESTO ============
AUTH_TOKEN = "TU_TOKEN_AQUI"  # Token Bearer de la sesion (~24h); copiarlo de F12 -> Network -> api-pao.utpxpedition.com
USER_ID = "TU_USER_ID_AQUI"
TENANT_ID = "TU_TENANT_ID_AQUI"

COURSES = [
    ("Mecánica Clásica", "TU_COURSE_ID_AQUI", "TU_SECTION_ID_AQUI"),  # Ejemplo; ver README "Uso actual"
    # ("Otro_Curso", "COURSE_ID", "SECTION_ID"),
]

OUTPUT_DIR = "./descargas_utp"

# QuÃ© formatos descargar cuando un mismo material viene repetido en varios
# (ej. Video demostrativo trae MP4 + MP3-solo-audio + PDF-guion del mismo contenido).
# Quita extensiones de esta lista si no las quieres (ej. quita "mp3" para ahorrar espacio).
DOWNLOAD_EXTENSIONS = {"pdf", "mp4", "docx", "xlsx", "pptx", "png", "jpg", "jpeg"}
# mp3 excluido por defecto -> es el mismo audio que ya viene en el mp4
# ==========================================

API_BASE = "https://api-pao.utpxpedition.com/course/student/courses"

HEADERS = {
    "accept": "*/*",
    "authorization": f"Bearer {AUTH_TOKEN}",
    "origin": "https://class.utp.edu.pe",
    "referer": "https://class.utp.edu.pe/",
    "transaction-id": "00000000-0000-0000-0000-000000000000",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "user-id": USER_ID,
    "user-role": "STUDENT",
    "x-tenant-id": TENANT_ID,
}

# Solo capturamos archivos reales del bucket de almacenamiento de UTP.
# Esto evita que se cuelen Ã­conos de la interfaz (alert-circle, file-text,
# film, link, music, etc.) que vienen de otros dominios/CDN y que tambiÃ©n
# terminan en .png/.jpg pero NO son material del curso.
UTP_FILE_DOMAIN = "utp-prd-upload-file-storage.s3.amazonaws.com"
FILE_EXT_RE = re.compile(
    r'https?://' + re.escape(UTP_FILE_DOMAIN) + r'/[^\s"\'<>]+?\.(pdf|mp4|mp3|docx?|xlsx?|pptx?|png|jpe?g)',
    re.IGNORECASE,
)

console = Console()


# ---------- Estado global para la UI ----------
@dataclass
class Stats:
    downloaded: int = 0
    skipped_existing: int = 0
    skipped_format: int = 0
    errors: int = 0
    current_course: str = ""
    current_week: str = ""
    current_file: str = ""
    course_done: int = 0
    course_total: int = 0
    log: list = field(default_factory=list)

    def push_log(self, msg: str, max_lines: int = 8):
        self.log.append(msg)
        if len(self.log) > max_lines:
            self.log.pop(0)


STATS = Stats()


def sanitize(name: str, max_len: int = 120) -> str:
    name = unquote(name)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", " ", name).strip(" ._")
    return name[:max_len] if name else "sin_nombre"


def get_section_full(course_id: str, section_id: str) -> dict:
    url = f"{API_BASE}/{course_id}/sections/{section_id}/full"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()["data"]


def extract_urls_from_html(html: str) -> list:
    """Devuelve lista de (url, ext) Ãºnicos preservando orden."""
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


def download_file(url: str, ext: str, dest_folder: str, fallback_name: str) -> str:
    """Devuelve: 'ok' | 'skip_exist' | 'error'"""
    os.makedirs(dest_folder, exist_ok=True)
    parsed_name = sanitize(os.path.basename(urlparse(url).path)) or f"{fallback_name}.{ext}"
    dest_path = os.path.join(dest_folder, parsed_name)

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
        return f"error: {e}", parsed_name


def text_progress_bar(done: int, total: int, width: int = 40) -> str:
    if total <= 0:
        return "[dim]sin datos aÃºn...[/]"
    frac = min(done / total, 1.0)
    filled = int(width * frac)
    bar = "â–ˆ" * filled + "â–‘" * (width - filled)
    pct = int(frac * 100)
    return f"[cyan]{bar}[/] {pct:3d}%  ({done}/{total})"


def build_view() -> Group:
    """Construye la vista completa como un simple stack de renderables,
    sin usar Layout de pantalla completa (mÃ¡s compatible con distintos
    terminales, incluyendo los embebidos en apps de escritorio)."""

    header = Panel(
        Text("ðŸ“š UTP+class Material Downloader", justify="center", style="bold cyan"),
        style="cyan",
    )

    status_table = Table.grid(padding=(0, 2))
    status_table.add_column(style="bold")
    status_table.add_column()
    status_table.add_row("Curso actual:", STATS.current_course or "-")
    status_table.add_row("Progreso curso:", text_progress_bar(STATS.course_done, STATS.course_total))
    status_table.add_row("Semana/Tema:", STATS.current_week or "-")
    status_table.add_row("Archivo:", STATS.current_file or "-")

    log_lines = STATS.log or ["..."]
    log_text = Text.from_markup("\n".join(log_lines))

    footer_table = Table.grid(padding=(0, 3), expand=True)
    footer_table.add_column(justify="center")
    footer_table.add_column(justify="center")
    footer_table.add_column(justify="center")
    footer_table.add_column(justify="center")
    footer_table.add_row(
        f"[green]âœ… Descargados: {STATS.downloaded}[/]",
        f"[yellow]â­ï¸  Ya existÃ­an: {STATS.skipped_existing}[/]",
        f"[dim]ðŸš« Filtrados por formato: {STATS.skipped_format}[/]",
        f"[red]âŒ Errores: {STATS.errors}[/]",
    )

    return Group(
        header,
        Panel(status_table, title="Estado", border_style="blue"),
        Panel(log_text, title="Registro", border_style="magenta", height=len(log_lines) + 2),
        Panel(footer_table, border_style="dim"),
    )


def process_course(course_name: str, course_id: str, section_id: str, live: Live):
    STATS.current_course = course_name
    STATS.course_done = 0
    STATS.course_total = 0
    STATS.push_log(f"[cyan]â–¶ Cargando estructura de '{course_name}'...[/]")
    live.update(build_view())

    try:
        data = get_section_full(course_id, section_id)
    except Exception as e:
        STATS.push_log(f"[red]âœ— Error al cargar '{course_name}': {e}[/]")
        STATS.errors += 1
        live.update(build_view())
        return

    course_folder = os.path.join(OUTPUT_DIR, sanitize(course_name))

    # Precontar total de archivos para la barra de progreso
    all_jobs = []
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
                    all_jobs.append((week_label, title, theme_folder, url, ext))

    STATS.course_total = len(all_jobs)
    live.update(build_view())

    for week_label, title, theme_folder, url, ext in all_jobs:
        STATS.current_week = f"{week_label} â€” {title}"

        if ext.lower() not in DOWNLOAD_EXTENSIONS:
            STATS.skipped_format += 1
            STATS.course_done += 1
            live.update(build_view())
            continue

        STATS.current_file = os.path.basename(urlparse(url).path)
        live.update(build_view())
        result, filename = download_file(url, ext, theme_folder, sanitize(title))

        if result == "ok":
            STATS.downloaded += 1
            STATS.push_log(f"[green]âœ“[/] {week_label}: {filename}")
        elif result == "skip_exist":
            STATS.skipped_existing += 1
            STATS.push_log(f"[yellow]â­[/] {week_label}: {filename} (ya existe)")
        else:
            STATS.errors += 1
            STATS.push_log(f"[red]âœ—[/] {week_label}: {filename} â€” {result}")

        STATS.course_done += 1
        live.update(build_view())
        time.sleep(0.1)


def main():
    if "PEGA_AQUI" in AUTH_TOKEN:
        console.print("[bold red]âš ï¸  Antes de correr el script, rellena AUTH_TOKEN, USER_ID y TENANT_ID en el archivo.[/]")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # screen=False: se actualiza "en el mismo lugar" en vez de tomar la pantalla
    # completa. Esto es mucho mÃ¡s compatible con terminales embebidas (IDEs,
    # apps de escritorio) que no reportan bien su tamaÃ±o.
    with Live(build_view(), console=console, refresh_per_second=6, screen=False) as live:
        for course_name, course_id, section_id in COURSES:
            process_course(course_name, course_id, section_id, live)
        live.update(build_view())

    console.print(Panel(
        f"[bold green]âœ… Listo![/]\n\n"
        f"Descargados: {STATS.downloaded}\n"
        f"Ya existÃ­an: {STATS.skipped_existing}\n"
        f"Filtrados por formato: {STATS.skipped_format}\n"
        f"Errores: {STATS.errors}\n\n"
        f"Carpeta: {os.path.abspath(OUTPUT_DIR)}",
        title="Resumen final",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
