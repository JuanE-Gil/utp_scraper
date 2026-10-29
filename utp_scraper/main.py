# utp_scraper.main — punto de entrada (port de v2.2:291-315 adaptado al contrato de eventos).
# Credenciales SOLO por variables de entorno (README §Seguridad).

import os
import sys

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from utp_scraper.api import build_headers, get_section_full
from utp_scraper.core import collect_jobs, run_jobs
from utp_scraper.courses import COURSES
from utp_scraper.ui_cli import UiState, build_view

console = Console()
OUTPUT_DIR = "./descargas_utp"


def make_handler(state: UiState, apply_view):
    """Devuelve la función on_event(nombre, **kwargs) que consume core.run_jobs."""

    def on_event(name, **kw):
        if name == "downloaded":
            state.downloaded += 1
            state.current_file = kw.get("filename") or state.current_file
            state.push_log(f"[green]✓[/] {kw.get('week')}: {kw.get('filename')}")
        elif name == "skipped_existing":
            state.skipped_existing += 1
            state.push_log(f"[yellow]⏭[/] {kw.get('week')}: {kw.get('filename')} (ya existe)")
        elif name == "error":
            state.errors += 1
            state.push_log(f"[red]✗[/] {kw.get('week')}: {kw.get('filename')} — {kw.get('detail')}")
        elif name == "filtered_format":
            state.skipped_format += 1
            state.push_log(f"[dim]⏹[/] {kw.get('week')}: formato .{kw.get('ext')} fuera de lista")
        state.current_week = kw.get("week") or state.current_week
        state.course_done += 0 if name == "course_started" else 1
        apply_view()

    return on_event


def main():
    creds = [os.environ.get(k, "") for k in ("AUTH_TOKEN", "USER_ID", "TENANT_ID")]
    if not all(creds):
        console.print(
            "[bold red]⚠ Faltan credenciales: define AUTH_TOKEN, USER_ID y TENANT_ID como variables de entorno "
            "(ver README §Seguridad — el token equivale a la contraseña).[/]"
        )
        raise SystemExit(1)
    auth_token, user_id, tenant_id = creds
    headers = build_headers(auth_token, user_id, tenant_id)

    state = UiState()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # screen=False: compatible con terminales embebidas (docs de v2.2:298-300).
    with Live(build_view(state), console=console, refresh_per_second=6, screen=False) as live:
        def apply_view():
            live.update(build_view(state))

        for course_name, course_id, section_id in COURSES:
            state.current_course = course_name
            state.course_done = 0
            state.course_total = 0
            state.push_log(f"[cyan]▶ Cargando estructura de '{course_name}'...[/]")
            apply_view()
            try:
                data = get_section_full(course_id, section_id, headers)
            except Exception as e:
                state.push_log(f"[red]✗ Error al cargar '{course_name}': {e}[/]")
                state.errors += 1
                apply_view()
                continue
            jobs = collect_jobs(data, course_name)
            state.course_total = len(jobs)
            apply_view()
            run_jobs(jobs, OUTPUT_DIR, make_handler(state, apply_view))
            state.current_course = None

    console.print(
        Panel(
            Text.from_markup(
                f"[bold green]✔ Listo![/]\n\n"
                f"Descargados: {state.downloaded}\n"
                f"Ya existían: {state.skipped_existing}\n"
                f"Filtrados por formato: {state.skipped_format}\n"
                f"Errores: {state.errors}\n\n"
                f"Carpeta: {os.path.abspath(OUTPUT_DIR)}"
            ),
            title="Resumen final",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()
