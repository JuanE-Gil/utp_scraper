# utp_scraper.ui_cli — presentación en terminal usando rich; consume el estado
# que main alimenta con eventos de core (port verbatim de v2.2:166-215).

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class UiState:
    def __init__(self):
        self.current_course = None
        self.current_week = None
        self.current_file = None
        self.course_done = 0
        self.course_total = 0
        self.downloaded = 0
        self.skipped_existing = 0
        self.skipped_format = 0
        self.errors = 0
        self.log = []

    def push_log(self, line: str):
        self.log.append(line)
        self.log = self.log[-8:]


def text_progress_bar(done: int, total: int, width: int = 40) -> str:
    if total <= 0:
        return "[dim]sin datos aún...[/]"
    frac = min(done / total, 1.0)
    filled = int(width * frac)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(frac * 100)
    return f"[cyan]{bar}[/] {pct:3d}%  ({done}/{total})"


def build_view(state: UiState) -> Group:
    header = Panel(
        Text("📚 UTP+class Material Downloader", justify="center", style="bold cyan"),
        style="cyan",
    )

    status_table = Table.grid(padding=(0, 2))
    status_table.add_column(style="bold")
    status_table.add_column()
    status_table.add_row("Curso actual:", state.current_course or "-")
    status_table.add_row("Progreso curso:", text_progress_bar(state.course_done, state.course_total))
    status_table.add_row("Semana/Tema:", state.current_week or "-")
    status_table.add_row("Archivo:", state.current_file or "-")

    log_lines = state.log or ["..."]
    log_text = Text.from_markup("\n".join(log_lines))

    footer_table = Table.grid(padding=(0, 3), expand=True)
    footer_table.add_column(justify="center")
    footer_table.add_column(justify="center")
    footer_table.add_column(justify="center")
    footer_table.add_column(justify="center")
    footer_table.add_row(
        f"[green]✅ Descargados: {state.downloaded}[/]",
        f"[yellow]⏭ Ya existían: {state.skipped_existing}[/]",
        f"[dim]🚫 Filtrados por formato: {state.skipped_format}[/]",
        f"[red]❌ Errores: {state.errors}[/]",
    )

    return Group(
        header,
        Panel(status_table, title="Estado", border_style="blue"),
        Panel(log_text, title="Registro", border_style="magenta", height=len(log_lines) + 2),
        Panel(footer_table, border_style="dim"),
    )
