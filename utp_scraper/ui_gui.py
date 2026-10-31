# utp_scraper.ui_gui — GUI v2 (rediseño D1–D4 del plan de diseño, nivel Tk A).
# Una sola ventana con 4 vistas intercambiables sobre un marco persistente (§6):
# cabecera con marca + pasos + chip de sesión, pie con versión y estado breve.
# Solo consume auth/api/core por el contrato de eventos: cero lógica de descargas aquí.
# Concurrencia: login y descarga corren en hilos; la GUI drena queue.Queue desde
# su propio bucle read(timeout=) y nunca se bloquea.
# Secretos: la contraseña vive solo en el campo y en la llamada login() (AGENTS.md).

import os
import queue
import threading

import FreeSimpleGUI as sg

from utp_scraper import api, core
from utp_scraper import ui_theme as th
from utp_scraper.auth import AuthError, login

DEFAULT_OUTPUT = os.path.join(os.getcwd(), "descargas_utp")

# (clave de core, etiqueta TUI §9, etiqueta corta para chips, estado §5.1)
COUNTERS = (("ok", "Descargados", "Descargados", th.OK),
            ("skip_exist", "Ya existían", "Ya existían", th.WARN),
            ("filtered_format", "Filtrados por formato", "Filtrados", th.INFO),
            ("error", "Errores", "Errores", th.ERR))
WORD = {"downloaded": ("Descargado", th.OK),
        "skipped_existing": ("Ya existía", th.WARN),
        "filtered_format": ("Filtrado", th.INFO),
        "error": ("Error", th.ERR)}


def _half_trunc(s, n=64):
    """Nombre largo truncado por el medio con puntos suspensivos (§8.5)."""
    if len(s) <= n:
        return s
    h = (n - 1) // 2
    return s[:h] + "…" + s[len(s) - (n - h):]


def _fetch_all(session):
    """Matrícula + períodos → (grupos, excluidos, error). Nunca lanza."""
    try:
        courses = api.list_dashboard_courses(session.user_id, session.headers)
    except Exception as e:
        return None, [], str(e)
    try:
        periods = api.list_academic_periods(session.user_id, session.headers)
    except Exception:
        periods = None  # respaldo documentado en group_courses_by_period
    groups, excluded = core.group_courses_by_period(courses, periods)
    return groups, excluded, None


def _worker(session, selection, root, q):
    """Hilo de descargas: mínima lógica; todo estado va por la cola (§4.4)."""
    for course in selection:
        try:
            data = api.get_section_full(
                course["course_id"], course["section_id"], session.headers)
        except Exception as e:
            q.put(("error_curso", {"curso": course["name"], "detail": str(e)}))
            continue
        jobs = core.collect_jobs(data, course["name"], folder=course["folder"])
        core.run_jobs(jobs, root, lambda name, **kw: q.put((name, kw)),
                      course=course["name"])
    q.put(("fin", {}))


# ─── Marco persistente (§6.2) ────────────────────────────────────────────────

def _set_steps(w, cur):
    for i, name in enumerate(th.STEPS):
        w[f"-STEP{i}-"].update(
            ("✓ " if i < cur else "● " if i == cur else "○ ") + name,
            text_color=(th.VIOL if i < cur else th.BLUE if i == cur else th.INK3),
            font=("Segoe UI", 9, "bold" if i <= cur else "normal"))


def _make_window():
    th.theme()
    steps = [sg.Text(f"○ {name}", key=f"-STEP{i}-", font=th.CAP, text_color=th.INK3,
                     pad=(6, 4)) for i, name in enumerate(th.STEPS)]
    header = [sg.Text(th.BRAND, font=th.SEC, text_color=th.INK, pad=(0, 0)),
              sg.Push(), *steps, sg.Push(),
              sg.Text("", key="-SESS-", font=th.CAP, text_color=th.INK2, pad=(8, 4)),
              th.btnT("Cerrar sesión", key="-LOGOUT-", visible=False)]
    body = sg.Column([[sg.Text("", visible=False)]], key="-BODY-",
                     expand_x=True, expand_y=True)
    footer = [th.capt(th.VERSION, p=(0, 0)), sg.Push(),
              sg.Text("", key="-ST-", font=th.CAP, text_color=th.INK2, pad=(0, 0))]
    w = sg.Window(
        th.BRAND + " — Acceso · Cursos · Descarga · Resumen",
        [[sg.Column([header], background_color=th.BG, pad=(0, 8), expand_x=True)],
         [body],
         [sg.Column([footer], background_color=th.BG, pad=(0, 8), expand_x=True)]],
        size=(1040, 720), resizable=True, margins=(24, 16),
        enable_close_attempted_event=True, finalize=True)
    w.set_min_size((860, 600))
    return w


def _show(w, st, name, rows_fn):
    """Muestra la vista `name`; construye las filas solo la primera vez."""
    if st["cur"]:
        w[st["cur"]].update(visible=False)
    if name not in st["views"]:
        vk = f"-V{st['nc']}{name}-"
        st["nc"] += 1
        st["views"][name] = vk
        # sg.pin: sin él, el Column oculto sigue reservando su alto en Tk
        w.extend_layout(st["body"], [[sg.pin(sg.Column(
            rows_fn(), key=vk, background_color=th.BG, pad=(4, 0),
            expand_x=True, expand_y=True))]])
    st["cur"] = st["views"][name]
    w[st["cur"]].update(visible=True)


# ─── Vista 1 · Acceso (§7.1) ─────────────────────────────────────────────────

def _rows_acceso():
    card = th.card([
        [th.ttl("Inicia sesión", p=(0, (8, 4)))],
        [th.capt("Usa tu código y clave de UTP+class", p=(0, (0, 16)))],
        [th.txt("Código de usuario", p=(0, (12, 4)))],
        [sg.Input("", key="-USER-", size=(26, 1), font=th.BODY, pad=(0, 4))],
        [th.txt("Contraseña", p=(0, (12, 4)))],
        [sg.Input("", key="-PASS-", size=(24, 1), font=th.BODY, pad=(0, 6),
                  password_char="•"),
         th.btnT("Ver", key="-EYE-", p=(8, (12, 6)))],
        # espacio reservado: el formulario no cambia de alto al aparecer un error (§7.1)
        [sg.Text("", key="-MSG-", size=(44, 2), font=th.CAP, pad=(0, (8, 0)))],
        [th.btnP("Entrar", key="-GO-", expand_x=True, brk=True)],
        [th.capt("Tu contraseña no se guarda. Solo se accede a tus propios cursos.",
                 p=(0, (12, 8)))],
    ])
    return [[sg.VPush()],
            [sg.Push(), card, sg.Push()],
            [sg.VPush()]]


def _login_async(q, user, pwd):
    try:
        q.put(("ok", login(user, pwd)))
    except AuthError as ex:
        q.put(("err", str(ex)))
    except Exception as ex:  # sin conexión: mismo banner, otro texto (§9)
        q.put(("err", "No se pudo conectar. Revisa tu conexión e inténtalo de nuevo."
               if "connection" in str(ex).lower() or "timed out" in str(ex).lower()
               else str(ex)))


def _acceso(w, st):
    """True = hay sesión; False = salir de la app."""
    _show(w, st, "acceso", _rows_acceso)
    _set_steps(w, 0)
    w["-SESS-"].update("")
    w["-LOGOUT-"].update(visible=False)
    w["-ST-"].update("Sin sesión")
    w["-MSG-"].update("", text_color=th.INK2)
    w["-USER-"].update("", disabled=False)
    w["-PASS-"].update("", disabled=False)
    w["-GO-"].update("Entrar", disabled=False)
    w["-USER-"].set_focus()
    q = queue.Queue()
    eye_open = False
    while True:
        e, v = w.read(timeout=25)
        try:
            kind, payload = q.get_nowait()
        except queue.Empty:
            kind = None
        if kind == "ok":
            st["session"] = payload
            st["user"] = (v.get("-USER-") or "").strip()
            w["-SESS-"].update("Código: " + st["user"])
            w["-LOGOUT-"].update(visible=True)
            w["-ST-"].update("Sesión activa")
            return True
        if kind == "err":
            w["-MSG-"].update(text_color=th.ERR[1],
                              value=f"{payload} No se reintentará automáticamente "
                                    "para evitar bloquear tu cuenta.")
            _unbusy(w)
            continue
        if kind is not None:
            continue
        if e in (sg.WIN_CLOSED, None):
            return False
        if e == sg.WIN_CLOSE_ATTEMPTED_EVENT:
            return False
        if e == sg.TIMEOUT_KEY:
            continue
        if e == "-EYE-":
            eye_open = not eye_open
            w["-PASS-"].update(password_char="" if eye_open else "•")
            continue
        if e in ("-GO-", "-USER-", "-PASS-"):
            user = (v.get("-USER-") or "").strip()
            pwd = v.get("-PASS-") or ""
            if not user or not pwd:
                w["-MSG-"].update("Completa tu código y tu contraseña.")
                continue
            w["-MSG-"].update("")
            w["-GO-"].update("Autenticando…", disabled=True)
            w["-USER-"].update(disabled=True)
            w["-PASS-"].update(disabled=True)
            threading.Thread(target=_login_async, args=(q, user, pwd),
                             daemon=True).start()


def _unbusy(w):
    w["-GO-"].update(disabled=False)
    w["-USER-"].update(disabled=False)
    w["-PASS-"].update(disabled=False)


# ─── Vista 2 · Cursos (§7.2) ─────────────────────────────────────────────────

def _rows_cursos(st, cp):
    st["order"] = []      # [(chk_key, curso)] del build actual
    st["gmeta"] = []      # por grupo: checks / head / col / open
    st["cp"] = cp
    list_rows, gmeta = [], st["gmeta"]
    for gi, g in enumerate(st["groups"] or []):
        checks, body = [], []
        for j, c in enumerate(g["courses"]):
            ck = f"{cp}K{gi}_{j}"
            cls = "Clase " + str(c["class_number"]) if c.get("class_number") else ""
            fila = sg.Column([[sg.Check(c["name"], key=ck, default=bool(g["is_current"]),
                                        enable_events=True, checkbox_color=th.BLUE,
                                        font=th.BODY, pad=(0, 2),
                                        background_color=th.BG),
                               sg.Push(),
                               th.capt(cls, p=(16, 2), tc=th.INK2)]],
                             pad=(0, 2), key=f"{cp}R{gi}_{j}")
            # sg.pin: fila puede ocultarse por el filtro y soltar su alto
            body.append([sg.pin(fila)])
            checks.append(ck)
            st["order"].append((ck, c))
        hdr = [[th.btnT(("▾ " if g["is_current"] else "▸ ") + g["label"],
                        key=f"{cp}G{gi}", bgc=th.SURFACE_ALT),
                th.chip("vigente", (th.VIOL_L, th.VIOL_D)) if g["is_current"]
                else sg.Text("", pad=(2, 2)),
                th.chip(f"{len(checks)} curso" + ("s" if len(checks) != 1 else "")),
                sg.Push(),
                th.btnT("Seleccionar todo", key=f"{cp}A{gi}", bgc=th.SURFACE_ALT)]]
        list_rows.append([sg.Column(hdr, background_color=th.SURFACE_ALT,
                                    pad=((0, 4), (12, 2)), expand_x=True)])
        # sg.pin: al colapsar el ciclo, su cuerpo suelta el alto (defecto capturas)
        list_rows.append([sg.pin(sg.Column(body, key=f"{cp}GC{gi}",
                                           pad=((24, 0), (0, 8)),
                                           visible=bool(g["is_current"])))])
        gmeta.append({"checks": checks, "open": bool(g["is_current"]),
                      "head": f"{cp}G{gi}", "col": f"{cp}GC{gi}"})

    if not list_rows:
        list_rows = [[th.banner("No tienes cursos matriculados este período.",
                                estado=th.INFO)]]
    if st.get("excluded"):
        names = ", ".join(c.get("name") or "sin nombre" for c in st["excluded"])
        list_rows.append([th.banner(
            f"{len(st['excluded'])} cursos no se pueden descargar "
            f"(sin identificador válido): {names}", estado=th.WARN)])

    scroll = sg.Column(list_rows, scrollable=True, vertical_scroll_only=True,
                       size=(940, 460), expand_x=True, expand_y=True,
                       sbar_trough_color=th.SURFACE_ALT, sbar_arrow_color=th.INK2)
    return [
        [th.ttl("Tus cursos"), sg.Push(), th.btnT("Actualizar", key=f"{cp}REFRESH")],
        [th.capt("Elige qué descargar. Se pre-marca el ciclo vigente.", p=(0, (0, 8)))],
        [sg.Input("", key=f"{cp}BQ", enable_events=True, size=(36, 1), font=th.BODY,
                  pad=(0, (4, 8)), expand_x=True)],
        [scroll],
        [th.txt("Destino", p=(0, (12, 4))),
         sg.Input(st.get("root", DEFAULT_OUTPUT), key=f"{cp}ROOT", expand_x=True,
                  font=th.MONO, pad=(8, (12, 4))),
         sg.FolderBrowse("Cambiar", key=f"{cp}DIR", font=th.CAP, pad=(8, (12, 4)))],
        [sg.Push(), th.capt("", key=f"{cp}SEL", p=(0, (12, 4))),
         th.btnP("Descargar", key=f"{cp}DL", dis=True)],
    ]


def _selcount(w, st, cp):
    return sum(1 for ck, _c in st["order"] if ck.startswith(cp) and w[ck].get())


def _sync_counter(w, st, cp):
    n = _selcount(w, st, cp)
    w[f"{cp}SEL"].update(f"{n} seleccionado" + ("s" if n != 1 else "")
                         if n else "Selecciona al menos un curso.")
    w[f"{cp}DL"].update((f"Descargar {n} curso" + ("s" if n != 1 else ""))
                        if n else "Descargar", disabled=(n == 0))


def _cursos(w, st):
    """Vista Cursos: 'dl' | 'out' (cerrar sesión) | None (salir de la app)."""
    while True:  # garantiza matrícula; Reintentar cae aquí mismo
        if st.get("groups") is None:
            # shortcut: fetch síncrono; congela ~1–2 s. A hilo cuando D4/D8 lo pidan.
            w["-ST-"].update("Cargando tus cursos…")
            w.Refresh()
            st["groups"], st["excluded"], st["ferr"] = _fetch_all(st["session"])
            if st["groups"] is None:
                if sg.popup_yes_no("No se pudo listar la matrícula: "
                                   + (st["ferr"] or "") + "\n¿Volver al acceso?",
                                   title="Matrícula", default_button="Reintentar") == "Yes":
                    return "out"
                continue
            st["views"].pop("cursos", None)  # fuerza rebuild el build con datos
        p = st["p"] = f"C{st['nc']}-"
        _set_steps(w, 1)
        _show(w, st, "cursos", lambda: _rows_cursos(st, p))
        w["-ST-"].update("Elige qué descargar")
        _sync_counter(w, st, p)

        leave = False
        while not leave:
            e, v = w.read(timeout=25)
            if e in (sg.WIN_CLOSED, None):
                return None
            if e == sg.WIN_CLOSE_ATTEMPTED_EVENT:
                return None
            if e == sg.TIMEOUT_KEY:
                continue
            if e == "-LOGOUT-":
                st["session"] = None
                st["groups"] = None
                return "out"
            if e == f"{p}REFRESH":
                st["groups"] = None
                leave = True  # vuelve arriba: refetch + rebuild
            elif e == f"{p}BQ":
                _apply_filter(w, st, p, (v.get(f"{p}BQ") or "").strip().lower())
            elif e.startswith(f"{p}G"):
                gi = int(e[len(p) + 1:])
                g = st["gmeta"][gi]
                g["open"] = not g["open"]
                w[e].update(("▾ " if g["open"] else "▸ ") + st["groups"][gi]["label"])
                w[g["col"]].update(visible=g["open"])
            elif e.startswith(f"{p}A"):
                gi = int(e[len(p) + 1:])
                g = st["gmeta"][gi]
                on = not all(w[ck].get() for ck in g["checks"])
                for ck in g["checks"]:
                    w[ck].update(on)
                _sync_counter(w, st, p)
            elif e == f"{p}DL":
                st["root"] = (v.get(f"{p}ROOT") or "").strip() or DEFAULT_OUTPUT
                st["selection"] = [c for ck, c in st["order"] if w[ck].get()]
                return "dl"
            elif e.startswith(f"{p}K"):
                _sync_counter(w, st, p)


def _apply_filter(w, st, p, query):
    for gi, g in enumerate(st["gmeta"]):
        vis = 0
        for ck in g["checks"]:
            course = next(c for k, c in st["order"] if k == ck)
            rowkey = f"{p}R" + ck[len(p) + 1:]  # misma j: K0_3 -> R0_3
            show = query in course["name"].lower()
            w[rowkey].update(visible=show)  # fila pin completa
            vis += show
        w[f"{p}G{gi}"].update(visible=vis > 0 or not query)
        w[g["col"]].update(visible=vis > 0 and g["open"])


# ─── Vista 3 · Descarga (§7.3) ───────────────────────────────────────────────

def _rows_descarga(p):
    def bar(k):
        return sg.ProgressBar(max_value=1, bar_color=(th.BLUE, th.BAR_TRACK),
                              size=(430, 12), key=k, pad=(0, 4))

    chips = [th.chip(f"0 · {lbl}", (th.BORDER, th.INK3), key=f"{p}CH{i}")
             for i, (_k, _t, lbl, _e) in enumerate(COUNTERS)]
    log = sg.Multiline("", key=f"{p}LOG", autoscroll=True, font=th.MONO,
                       background_color=th.SURFACE_ALT, text_color=th.INK,
                       size=(96, 10), pad=(0, 4))
    return [
        [th.ttl("Descargando")],
        [th.card([
            [th.txt("Avance general", font=th.SEC), sg.Push(),
             th.capt("0 %", key=f"{p}PCG", font=("Segoe UI", 12), tc=th.INK)],
            [bar(f"{p}PBG")],
            [th.capt("", key=f"{p}GEN")],
        ])],
        [th.card([
            [th.txt("", key=f"{p}CURSO", font=th.SEC, expand_x=True), sg.Push(),
             th.capt("", key=f"{p}PCC")],
            [bar(f"{p}PBC")],
            [th.txt("", key=f"{p}FILER", font=th.MONO, n=(60, 1))],
        ], p=((0, 0), (10, 1)))],
        [sg.Push(), *chips],
        [sg.Push(), th.btnT("Ver detalle", key=f"{p}LOGT")],
        [sg.pin(sg.Column([[log]], key=f"{p}LOGC", pad=((0, 0), (0, 8))))],
    ]


def _descarga(w, st):
    """Vista Descarga: dict de contadores al terminar; None si confirmó salir."""
    _set_steps(w, 2)
    w["-ST-"].update("Descargando…")
    p = f"D{st['nc']}-"
    _show(w, st, "descarga", lambda: _rows_descarga(p))
    q = queue.Queue()
    threading.Thread(target=_worker, daemon=True,
                     args=(st["session"], st["selection"], st["root"], q)).start()

    totals = {k: 0 for k, _t, _c, _e in COUNTERS}
    errores = []
    state = {"cdone": 0, "cur_name": "", "cur_total": 0, "cur_done": 0}
    csel = len(st["selection"])

    def chips_refresh():
        for i, (k, _t, lbl, est) in enumerate(COUNTERS):
            zero = totals[k] == 0
            w[f"{p}CH{i}"].update(f"{totals[k]} · {lbl}",
                                  background_color=(th.BORDER if zero else est[0]),
                                  text_color=(th.INK3 if zero else est[1]))

    def step_course(name, total):
        state.update(cur_name=name, cur_total=total, cur_done=0)
        w[f"{p}CURSO"].update(name)
        w[f"{p}GEN"].update(f"Curso {state['cdone'] + 1} de {csel}")
        w[f"{p}PCC"].update("0 %" if total else "Sin archivos")
        w[f"{p}FILER"].update("")
        try:
            w[f"{p}PBC"].UpdateBar(0, max=max(total, 1))
        except Exception:
            pass

    def finish_course(counts):
        for k in ("ok", "skip_exist", "error", "filtered_format"):
            totals[k] += counts.get(k, 0)
        state["cdone"] += 1
        w[f"{p}PCG"].update(f"{100 * state['cdone'] // max(csel, 1)} %")
        try:
            w[f"{p}PBG"].UpdateBar(state["cdone"], max=max(csel, 1))
        except Exception:
            pass
        chips_refresh()

    while True:
        e, v = w.read(timeout=25)
        try:
            ev, kw = q.get_nowait()
        except queue.Empty:
            ev, kw = None, None
        if ev is None and e in (sg.WIN_CLOSED, None):
            return None  # cierre sin confirmar (no debería ocurrir con close_attempted)
        if e == sg.WIN_CLOSE_ATTEMPTED_EVENT:
            if sg.popup_yes_no(
                    "Hay una descarga en curso. ¿Salir de todos modos? "
                    "Lo ya descargado se conserva.", title="Salir",
                    default_button="No") == "Yes":
                return None
            continue
        if ev is None:
            continue  # TIMEOUT u otros eventos de UI
        if ev == "course_started":
            step_course(kw.get("curso") or "", kw.get("total", 0))
            chips_refresh()
        elif ev == "file_started":
            w[f"{p}FILER"].update(_half_trunc(
                f"{kw.get('week', '')} · {kw.get('filename', '')}"))
        elif ev in WORD:
            word, est = WORD[ev]
            w[f"{p}LOG"].print(f"{word} · {kw.get('week', '')} · {_half_trunc(str(kw.get('filename') or kw.get('ext') or ''))}"
                               + (f" · {kw.get('detail')}" if kw.get("detail") else ""),
                               text_color=est[1])
            totals[ev] += 1
            state["cur_done"] += 1
            w[f"{p}PCC"].update(f"{state['cur_done']} de {max(state['cur_total'], 1)} "
                                "archivos" if state["cur_total"] else "Sin archivos")
            try:
                w[f"{p}PBC"].UpdateBar(state["cur_done"], max=max(state["cur_total"], 1))
            except Exception:
                pass
            chips_refresh()
        elif ev == "error_curso":
            w[f"{p}LOG"].print(f"Error · {kw['curso']}: contenido no disponible "
                               f"({kw['detail']})", text_color=th.ERR[1])
            errores.append(f"{kw['curso']}: {kw['detail']}")
            finish_course({"error": 1})
            w[f"{p}FILER"].update("")
        elif ev == "course_finished":
            finish_course(kw.get("conteos", {}))
            w[f"{p}FILER"].update("")
        elif ev == "fin":
            st["totals"], st["errores"] = totals, errores
            return totals


# ─── Vista 4 · Resumen (§7.4) ────────────────────────────────────────────────

def _rows_resumen(st, p, totals):
    err_n = totals.get("error", 0)
    title = "Descarga completada con errores" if err_n else "Descarga completada"
    rows = [
        [th.ttl(title)],  # nivel A: sin icono; color lo cuenta el bloque de cifras
        [th.capt(f"{len(st.get('selection') or [])} cursos procesados",
                 p=(0, (0, 12)))],
    ]
    figs, tabs = [], []
    for i, (k, lbl, _c, est) in enumerate(COUNTERS):
        zero = totals[k] == 0
        fig = th.txt(str(totals[k]), font=th.FIG,
                     tc=th.INK3 if zero else est[1], p=(0, 4))
        tab = th.capt(lbl, tc=th.INK2 if zero else est[1], p=(0, 0))
        figs.append(fig)
        tabs.append(tab)
    inner = [sg.Column([figs], background_color=th.SURFACE, pad=(12, 8)),
             sg.Column([tabs], background_color=th.SURFACE, pad=(12, 0))]
    rows.append([sg.Column([inner], background_color=th.BORDER, pad=(1, 1))])

    if err_n:
        err_rows = [[th.capt("— " + s, tc=th.ERR[1], p=(0, 2))]
                    for s in (st.get("errores") or [])[-30:]]
        rows += [
            [sg.Push(), sg.pin(sg.Column(err_rows, key=f"{p}ERRC", pad=((0, 0), (8, 8)),
                                         scrollable=True, vertical_scroll_only=True,
                                         size=(560, min(20 * max(len(err_rows), 1), 180)),
                                         visible=False))],
            [sg.Push(), th.btnT(f"Ver errores ({err_n})", k=f"{p}ERBT"), sg.Push()],
        ]

    rows += [
        [th.txt("Carpeta:", p=(0, (16, 4))),
         th.capt(os.path.abspath(st["root"]), tc=th.INK2, p=(8, (16, 4)))],
        [th.btnP("Abrir carpeta", key=f"{p}OPEN"),
         th.btnS("Volver a cursos", key=f"{p}BACK"),
         sg.Push(),
         th.btnT("Salir", key=f"{p}EXIT")],
    ]
    return rows


def _resumen(w, st, totals):
    """Vista Resumen: True = volver a cursos; False = salir."""
    _set_steps(w, 3)
    w["-ST-"].update("Listo")
    p = f"R{st['nc']}-"
    _show(w, st, "resumen", lambda: _rows_resumen(st, p, totals))
    while True:
        e, v = w.read(timeout=25)
        if e in (sg.WIN_CLOSED, None, f"{p}EXIT", sg.WIN_CLOSE_ATTEMPTED_EVENT):
            return False
        if e == sg.TIMEOUT_KEY:
            continue
        if e == "-LOGOUT-":
            return False
        if e == f"{p}OPEN":
            try:
                os.startfile(os.path.abspath(st["root"]))
            except Exception as ex:
                sg.popup("No se pudo abrir la carpeta en:\n"
                         + os.path.abspath(st["root"]), str(ex),
                         title="Abrir carpeta")
        elif e == f"{p}ERBT" and f"{p}ERRC" in w.AllKeysDict:
            vis = not w[f"{p}ERRC"].visible
            w[f"{p}ERRC"].update(visible=vis)
            w[e].update(f"Ocultar errores ({totals.get('error', 0)})"
                        if vis else f"Ver errores ({totals.get('error', 0)})")
        elif e == f"{p}BACK":
            return True


# ─── Bucle de la aplicación ──────────────────────────────────────────────────

def run():
    th.dpi_aware()
    st = {"session": None, "user": "", "groups": None, "excluded": [], "ferr": None,
          "root": DEFAULT_OUTPUT, "views": {}, "cur": None, "nc": 1, "body": None}
    w = _make_window()
    st["body"] = w["-BODY-"]
    salir = False
    try:
        while not salir:
            if not _acceso(w, st):
                break
            while True:
                r = _cursos(w, st)
                if r == "dl":
                    totals = _descarga(w, st)
                    if totals is None:
                        salir = True
                        break
                    if not _resumen(w, st, totals):
                        salir = True
                        break
                elif r == "out":
                    break           # cerrar sesión → Acceso
                else:
                    salir = True    # None = cerró X
                    break
    finally:
        w.close()
    return 0
