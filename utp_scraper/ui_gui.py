# utp_scraper.ui_gui — interfaz gráfica (Fase 2, plan §4.4).
# Solo consume auth/api/core por el contrato de eventos: cero lógica de descargas aquí.
# Concurrencia: la descarga corre en un hilo worker; la GUI drena una queue.Queue
# desde su propio bucle (read(timeout=)) y nunca se bloquea.
# Secreto: la contraseña vive solo en el campo y en la llamada login() (regla AGENTS.md).

import os
import queue
import threading

import FreeSimpleGUI as sg

from utp_scraper import api, core
from utp_scraper.auth import AuthError, login

DEFAULT_OUTPUT = os.path.join(os.getcwd(), "descargas_utp")


def _course_display(g: dict, c: dict) -> str:
    num = f" [{c['class_number']}]" if c.get("class_number") else ""
    tag = " · vigente" if g["is_current"] else ("" if not g["is_default"] else " (transversal)")
    return f"{g['label']}{tag} {c['name']}{num}"


def _fetch_groups(session):
    """Matrícula + períodos → grupos por ciclo (Épica B). Nunca lanza."""
    try:
        courses = api.list_dashboard_courses(session.user_id, session.headers)
    except Exception as e:
        return None, f"No se pudo listar la matrícula: {e}"
    try:
        periods = api.list_academic_periods(session.user_id, session.headers)
    except Exception:
        periods = None  # respaldo documentado en group_courses_by_period
    groups, _ = core.group_courses_by_period(courses, periods)
    return groups, None


def _login_window() -> "Session":
    layout = [
        [sg.Text("UTP+class Downloader", font=("SegoeUi", 14, "bold"))],
        [sg.Text("Usuario"), sg.Input(key="-USER-", size=(28, 1))],
        [sg.Text("Clave"), sg.Input(key="-PASS-", size=(28, 1), password_char="*")],
        [sg.Button("Entrar", key="-GO-"), sg.Button("Salir", key="-QUIT-")],
        [sg.Text("", size=(46, 2), key="-MSG-")],
    ]
    w = sg.Window("Login", layout, finalize=True)
    w["-USER-"].set_focus()
    session = None
    while session is None:
        ev, values = w.read()
        if ev in (sg.WIN_CLOSED, "-QUIT-"):
            break
        if ev == "-GO-":
            user, password = values.get("-USER-", "").strip(), values.get("-PASS-", "")
            if not user or not password:
                w["-MSG-"].update("Completa usuario y clave.")
                continue
            w["-MSG-"].update("Autenticando (1 llamada, sin navegador)...")
            try:
                session = login(user, password)
            except AuthError as e:
                w["-MSG-"].update(f"Login rechazado: {e}")
    w.close()
    return session


def _select_window(groups) -> tuple:
    """(seleccionada lista de records, root_dir) o ([], '') si se cierra."""
    order = []
    rows = []
    for g in groups:
        if g["courses"]:
            rows.append([sg.Text(g["label"] + (" · VIGENTE" if g["is_current"] else ""),
                                 font=("SegoeUi", 10, "bold"))])
            for c in g["courses"]:
                label = _course_display(g, c)
                key = f"-C{len(order)}-"
                rows.append([sg.Check(label, key, default=g["is_current"])])
                order.append((key, c))

    layout = rows + [
        [sg.Text("Destino"), sg.Input(DEFAULT_OUTPUT, key="-ROOT-", size=(34, 1)),
         sg.FolderBrowse("Elegir...")],
        [sg.Button("Descargar", key="-DL-"), sg.Button("Ahora no", key="-QUIT-")],
        [sg.Text("", size=(50, 1), key="-MSG-")],
    ]
    w = sg.Window("2 · Selección de cursos por ciclo", layout)
    selection, root = [], ""
    while True:
        ev, values = w.read()
        if ev in (sg.WIN_CLOSED, "-QUIT-"):
            break
        if ev == "-DL-":
            selection = [c for k, c in order if values.get(k)]
            root = values.get("-ROOT-", DEFAULT_OUTPUT).strip() or DEFAULT_OUTPUT
            if not selection:
                w["-MSG-"].update("Selecciona al menos un curso.")
                continue
            break
    w.close()
    return selection, root


def _worker(session, selection, root, q):
    """Hilo de descargas: mínima lógica, todos los estados van por la cola."""
    for course in selection:
        try:
            data = api.get_section_full(
                course["course_id"], course["section_id"], session.headers)
        except Exception as e:
            q.put(("error_curso", {"curso": course["name"], "detail": str(e)}))
            continue
        jobs = core.collect_jobs(data, course["name"], folder=course["folder"])
        q.put(("curso_jobs", {"curso": course["name"], "total": len(jobs)}))
        core.run_jobs(jobs, root, lambda name, **kw: q.put((name, kw)),
                      course=course["name"])
    q.put(("fin", {}))


def _progress_window(q):
    layout = [
        [sg.Text("", key="-CURSO-", font=("SegoeUi", 11, "bold")),
         sg.Text("", size=(70, 1), key="-FILE-")],
        [sg.ProgressBar(max_value=1, orientation="h", size=(62, 15), key="-PB-")],
        [sg.Button("Cancelar", key="-CANCEL-", disabled=True,
                   tooltip="Se habilita con Task 2.4 (cancelación)")],
        [sg.Multiline(size=(86, 16), key="-LOG-", autoscroll=True)],
    ]
    w = sg.Window("3 · Progreso", layout, finalize=True)
    done = False
    totals = {"ok": 0, "skip_exist": 0, "error": 0, "filtered_format": 0}
    # UI y cola se atienden en la misma vuelta: read(timeout=25) mantiene la
    # ventana viva y cada evento entra por get_nowait; el sleep(0.1) del worker
    # limita la tasa de eventos muy por debajo de 40/s.
    while not done:
        e, _ = w.read(timeout=25)
        if e in (sg.WIN_CLOSED, None):
            break
        try:
            ev, kw = q.get_nowait()
        except queue.Empty:
            continue
        if ev == "course_started":
            w["-CURSO-"].update(f"{kw.get('curso') or ''}")
            try:
                w["-PB-"].UpdateBar(0, max=max(kw.get("total", 0), 1))
            except Exception:
                pass
            w["-FILE-"].update("")
        elif ev == "file_started":
            w["-FILE-"].update(f"{kw.get('week')} | {kw.get('title')} -> {kw.get('filename')}")
        elif ev in ("downloaded", "skipped_existing", "error", "filtered_format"):
            icon = {"downloaded": "OK", "skipped_existing": "SKIP",
                    "error": "X", "filtered_format": "FMT"}[ev]
            w["-LOG-"].print(f"{icon} {kw.get('week')} | {kw.get('title')} | {kw.get('filename', kw.get('ext', ''))}"
                             + (f" ({kw.get('detail', '')})" if kw.get("detail") else ""))
        elif ev == "error_curso":
            w["-LOG-"].print(f"X {kw['curso']}: contenido no disponible ({kw['detail']})")
        elif ev == "course_finished":
            counts = kw.get("conteos", {})
            for k in totals:
                totals[k] += counts.get(k, 0)
            resumen = ", ".join(f"{k}={v}" for k, v in counts.items() if v)
            w["-LOG-"].print(f"— curso terminado: {resumen or 'sin archivos'}")
            w["-FILE-"].update("")
        elif ev == "fin":
            done = True
    # drena lo restante sin bloquear
    while True:
        try:
            ev, kw = q.get_nowait()
        except queue.Empty:
            break
        if ev == "course_finished":
            for k in totals:
                totals[k] += kw.get("conteos", {}).get(k, 0)
    w.close()
    return totals


def run():
    session = _login_window()
    if session is None:
        return 1
    groups, err = _fetch_groups(session)
    if groups is None:
        sg.PopupError(err, title="Matrícula")
        return 1
    selection, root = _select_window(groups)
    if not selection:
        return 0
    q = queue.Queue()
    threading.Thread(target=_worker, args=(session, selection, root, q), daemon=True).start()
    totals = _progress_window(q)
    sg.Popup(
        f"Descargados: {totals['ok']}\nYa existían: {totals['skip_exist']}\n"
        f"Filtrados: {totals['filtered_format']}\nErrores: {totals['error']}\n\n"
        f"Carpeta: {os.path.abspath(root)}",
        title="Resumen final",
    )
    return 0
