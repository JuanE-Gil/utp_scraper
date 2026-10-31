# tools/check_ui_redesign.py — autochequeo del rediseño GUI (constructs + ventana oculta).
# No interactúa: construye las 4 vistas, las monta en una ventana fuera de pantalla
# (location negativa), lee con timeout y cierra. Atrapa kwargs mal usados en tiempo real.
import FreeSimpleGUI as sg

import utp_scraper.ui_theme as th
import utp_scraper.ui_gui as g
from utp_scraper.core import group_courses_by_period

th.dpi_aware()
th.theme()

st = {"session": None, "user": "12345678", "groups": None, "excluded": [],
      "ferr": None, "root": "./descargas_utp", "views": {}, "cur": None, "nc": 1,
      "body": None}

# matrícula falsa: 1 ciclo vigente (2 cursos), 1 anterior (1), 1 transversal (1)
courses = [
    {"period": 202602, "acadCareer": "PREG", "module": "001", "name": "MECANICA CLASICA",
     "courseId": "c1", "sectionId": "s1", "classNumber": 41509},
    {"period": 202602, "acadCareer": "PREG", "module": "001", "name": "CALCULO I",
     "courseId": "c2", "sectionId": "s2", "classNumber": 33994},
    {"period": 202601, "acadCareer": "PREG", "module": "001", "name": "ESTRUCTURAS DE DATOS",
     "courseId": "c3", "sectionId": "s3", "classNumber": 1},
    {"period": 9999, "acadCareer": "PRED", "module": "011", "name": "TRANSVERSAL X",
     "courseId": "c4", "sectionId": "s4", "classNumber": None},
]
periods = [{"period": 202602, "acadCareer": "PREG", "module": "001",
            "name": "2026 - Ciclo 2 Agosto PREG (001)", "type": "CURRENT_PERIOD"},
           {"period": 202601, "acadCareer": "PREG", "module": "001",
            "name": "2026 - Ciclo 1 Marzo PREG (001)", "type": "PAST_PERIOD"},
           {"period": 9999, "acadCareer": "PRED", "module": "011", "name": None,
            "type": "DEFAULT"}]
st["groups"], st["excluded"] = group_courses_by_period(courses, periods)
assert len(st["groups"]) == 3, f"grupos: {len(st['groups'])}"

cp = "C1-"
login_rows = g._rows_acceso()
curso_rows = g._rows_cursos(st, cp)
desc_rows = g._rows_descarga("D1-")
totals = {"downloaded": 24, "skipped_existing": 3, "filtered_format": 71, "error": 0}
st["selection"] = [{"name": "x"}]
st["errores"] = []
print("layouts OK: acceso", len(login_rows), "cursos", len(curso_rows),
      "descarga", len(desc_rows))

# ventana real pero fuera de pantalla; nadie la ve
w = g._make_window()
st["body"] = w["-BODY-"]
w.move(-30000, -30000)

# 1) tema activo
assert sg.theme_background_color() == th.BG, sg.theme_background_color()

# 2) transición de vistas sin desplazamiento (sg.pin libera el espacio oculto)
g._show(w, st, "acceso", g._rows_acceso)
w.read(timeout=100)
ya = w[st["views"]["acceso"]].widget.winfo_rooty()
g._show(w, st, "cursos", lambda: g._rows_cursos(st, cp))
w.read(timeout=100)
yc = w[st["views"]["cursos"]].widget.winfo_rooty()
delta = yc - ya
assert abs(delta) <= 4, f"vista Cursos desplazada: delta {delta}px"
print(f"transicion acceso->cursos OK (delta {delta}px)")

# 3) acordeon: colapsar libera el alto y reabrir restaura el mapeo
def ysettle(w, key):
    """Lectura estabilizada (2 lecturas) — el canvas necesita tiempo."""
    w.read(timeout=150)
    w.refresh()
    w.read(timeout=150)
    return w[key].widget.winfo_rooty()

g1k, c0k = f"{cp}G1", f"{cp}GC0"
y_before = ysettle(w, g1k)
w[c0k].update(visible=False)
y_collapsed = ysettle(w, g1k)
assert y_collapsed - y_before < -8, f"colapso no libero: {y_collapsed - y_before}px"
w[c0k].update(visible=True)
y_re = ysettle(w, g1k)
assert w[c0k].widget.winfo_ismapped(), "cuerpo no re-aparece"
assert abs(y_re - y_before) <= 8, f"reabrir no devolvio el layout: {y_re - y_before}px"
print(f"acordeon OK (colapso libera {y_before - y_collapsed}px, reabre igual)")

# 4) filtro en vivo: solo el ciclo con coincidencias queda visible y desplegado
w[f"{cp}BQ"].update("MECANICA")
g._apply_filter(w, st, cp, "mecanica")
w.refresh()
w.read(timeout=150)
assert not w[f"{cp}G1"].widget.winfo_ismapped(), "ciclo sin match seguia visible"
assert w[f"{cp}GC0"].widget.winfo_ismapped(), "ciclo con match no se despliega"
w[f"{cp}BQ"].update("")
g._apply_filter(w, st, cp, "")
w.refresh()
w.read(timeout=150)
assert w[f"{cp}G1"].widget.winfo_ismapped(), "cabecera no volvio tras limpiar"
assert w[f"{cp}GC1"].widget.winfo_ismapped() == 0, "estado abierto no se restauro"
print("filtro OK (solo matchees visibles, restauracion correcta)")

# 5) seleccion: fila pintada y nombres en la barra de accion
ck_calc = next(ck for ck, c in st["order"] if "CALCULO" in c["name"].upper())
w[ck_calc].update(False)  # el vigente pre-marcado: apagar CALCULO
g._paint_rows(w, st, cp)
g._sync_counter(w, st, cp)
w.refresh()
w.read(timeout=100)
sel_txt = w[f"{cp}SEL"].get()
assert sel_txt.startswith("1 seleccionado: ") and "MECANICA" in sel_txt, sel_txt
rowbg = w[st["fila_map"][ck_calc]].widget.cget("background")
assert rowbg != th.BLUE_L, "fila sin check quedo pintada"
g_keys = [k for k, *_r in g.COUNTERS]
assert g_keys == ["downloaded", "skipped_existing", "filtered_format", "error"], g_keys
print("seleccion OK —", sel_txt)
print("contadores OK (eventos core):", g_keys)

# 6) marco: pasos, chip, contador
g._set_steps(w, 1)
g._sync_counter(w, st, cp)
for kchip in ("-STEP0-", "-STEP1-", "-ST-", "-SESS-", f"{cp}SEL",
              f"{cp}DL", f"{cp}BQ", f"{cp}ROOT"):
    assert kchip in w.AllKeysDict, kchip
w.read(timeout=300)
w.close()
print("window OK — tema, marco, pasos, chip y vista Cursos montados")
