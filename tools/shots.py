# tools/shots.py — captura las 4 vistas de la GUI con datos de ejemplo (Xvfb). No es parte de la suite.
# Uso: PYTHONPATH=. xvfb-run -a -s "-screen 0 1600x1000x24" python3 tools/shots.py <carpeta_salida>
import os
import sys

import FreeSimpleGUI as sg
from PIL import ImageGrab

import utp_scraper.ui_gui as g
import utp_scraper.ui_theme as th
from utp_scraper.core import group_courses_by_period

out = sys.argv[1] if len(sys.argv) > 1 else "shots"
os.makedirs(out, exist_ok=True)

th.dpi_aware()
th.theme()

NAMES = ["MECÁNICA CLÁSICA", "CÁLCULO I", "TALLER DE PROGRAMACIÓN", "DISEÑO DE PRODUCTOS Y SERVICIOS",
         "INGLÉS III", "LABORATORIO DE MECÁNICA CLÁSICA", "NEGOCIACIÓN Y NARRATIVA", "RUTA LABORAL"]
OLD1 = ["ADMINISTRACIÓN Y ORGANIZACIÓN DE EMPRESAS", "CIUDADANÍA Y REFLEXIÓN ÉTICA",
        "ESTADÍSTICA INFERENCIAL", "GESTIÓN DE PROYECTOS", "INTRODUCCIÓN A LAS TIC"]
OLD2 = ["COMPRENSIÓN Y REDACCIÓN DE TEXTOS II", "ESTADÍSTICA DESCRIPTIVA Y PROBABILIDADES",
        "HERRAMIENTAS INFORMÁTICAS PARA LA TOMA DE DECISIONES", "INGLÉS II"]
courses, n = [], 0
for period, names in (("2263", NAMES), ("2262", OLD1), ("2253", OLD2)):
    for nm in names:
        n += 1
        courses.append({"period": period, "acadCareer": "PREG", "module": "001", "name": nm,
                        "courseId": f"c{n}", "sectionId": f"s{n}", "classNumber": str(30000 + n * 137)})
courses.append({"period": "9999", "acadCareer": "PRED", "module": "011", "name": "CONOCE UTP CLASS",
                "courseId": "c99", "sectionId": "s99", "classNumber": "40001"})
periods = [{"period": "2263", "acadCareer": "PREG", "module": "001", "name": "2026 - Ciclo 2 Agosto PREG (001)", "type": "CURRENT_PERIOD"},
           {"period": "2262", "acadCareer": "PREG", "module": "001", "name": "2026 - Ciclo 1 Marzo PREG (001)", "type": "OLD_PERIOD"},
           {"period": "2253", "acadCareer": "PREG", "module": "001", "name": "2025 - Ciclo 2 Agosto PREG (001)", "type": "OLD_PERIOD"},
           {"period": "9999", "acadCareer": "PRED", "module": "011", "name": "PRED-MARZO25 (011)", "type": "OLD_PERIOD"}]
groups, excluded = group_courses_by_period(courses, periods)

st = {"session": None, "user": "u20210001", "groups": groups, "excluded": excluded, "ferr": None,
      "root": os.path.join(os.getcwd(), "descargas_utp"), "views": {}, "cur": None, "nc": 1, "body": None}
w = g._make_window()
st["body"] = w["-BODY-"]
w.move(20, 20)


def settle(n=3):
    for _ in range(n):
        w.read(timeout=120)
        w.refresh()


def snap(name):
    settle()
    t = w.TKroot
    x, y, wd, ht = t.winfo_rootx(), t.winfo_rooty(), t.winfo_width(), t.winfo_height()
    ImageGrab.grab(xdisplay=os.environ["DISPLAY"], bbox=(x, y, x + wd, y + ht)).save(f"{out}/{name}.png")
    print("shot", name, wd, "x", ht)


# 1 · Acceso
g._show(w, st, "acceso", g._rows_acceso)
g._set_steps(w, 0)
w["-ST-"].update("Sin sesión")
snap("1_acceso")

# 1b · Acceso con error
w["-USER-"].update("u20210001")
w["-MSG-"].update("Login rechazado (401): invalid_grant Invalid user credentials No se reintentará "
                  "automáticamente para evitar bloquear tu cuenta.", text_color=th.ERR[1])
snap("1b_acceso_error")

# 2 · Cursos
w["-SESS-"].update("Código: u20210001")
w["-LOGOUT-"].update(visible=True)
w["-ST-"].update("Elige qué descargar")
g._set_steps(w, 1)
p = "C1-"
g._show(w, st, "cursos", lambda: g._rows_cursos(st, p))
for ck, c in st["order"]:
    if c["name"] in ("MECÁNICA CLÁSICA", "CÁLCULO I", "TALLER DE PROGRAMACIÓN"):
        pass
    elif ck.startswith(p + "K0_"):
        w[ck].update(False)
g._paint_rows(w, st, p)
g._sync_counter(w, st, p)
snap("2_cursos")

# 2b · Cursos con ciclo anterior abierto
w[f"{p}G1"].update("▾ " + groups[1]["label"])
w[f"{p}GC1"].update(visible=True)
st["gmeta"][1]["open"] = True
snap("2b_cursos_anterior_abierto")

# 3 · Descarga
g._set_steps(w, 2)
w["-ST-"].update("Descargando…")
q = "D1-"
g._show(w, st, "descarga", lambda: g._rows_descarga(q))
w[f"{q}CURSO"].update("MECÁNICA CLÁSICA")
w[f"{q}GEN"].update("Curso 2 de 5")
w[f"{q}PCG"].update("40 %")
w[f"{q}PBG"].UpdateBar(2, max=5)
w[f"{q}PCC"].update("24 de 39 archivos")
w[f"{q}PBC"].UpdateBar(24, max=39)
w[f"{q}FILER"].update("Semana_07 · Semana_7-Video_HCJM.mp4")
for i, (k, _t, lbl, est) in enumerate(g.COUNTERS):
    val = (24, 3, 71, 1)[i]
    w[f"{q}CH{i}"].update(f"{val} · {lbl}", background_color=est[0], text_color=est[1])
lines = [("downloaded", "Semana_07 · Guion_TYBXNA.docx"), ("downloaded", "Semana_07 · Video_HCJM.mp4"),
         ("skipped_existing", "Semana_07 · Democracia.mp4"), ("filtered_format", "Semana_06 · Audio_01.mp3"),
         ("downloaded", "Semana_07 · Identidad_politica_JW.pdf"),
         ("error", "Semana_06 · video_corrupto.mp4 · timeout")]
for ev, txt in lines:
    word, est = g.WORD[ev]
    w[f"{q}LOG"].print(f"{word} · {txt}", text_color=est[1])
snap("3_descarga")

# 4 · Resumen
g._set_steps(w, 3)
w["-ST-"].update("Listo")
totals = {"downloaded": 142, "skipped_existing": 30, "filtered_format": 71, "error": 1}
st["selection"] = [c for _k, c in st["order"]][:5]
st["errores"] = ["Semana_06 · video_corrupto.mp4: timeout"]
r = "R1-"
g._show(w, st, "resumen", lambda: g._rows_resumen(st, r, totals))
snap("4_resumen")
w.close()