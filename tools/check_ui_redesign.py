# tools/check_ui_redesign.py — autochequeo del rediseño GUI ( constructs + ventana oculta).
# No interactúa: construye las 4 vistas, las monta en una ventana fuera de pantalla
# (location negativa), lee con timeout y cierra. Atrapa kwargs mal usados en tiempo real.
import FreeSimpleGUI as sg

import utp_scraper.ui_theme as th
import utp_scraper.ui_gui as g
from utp_scraper.core import group_courses_by_period

th.dpi_aware()
th.theme()

st = {"session": None, "user": "12345678", "groups": None, "excluded": [],
      "ferr": None, "root": "./descargas_utp", "views": {}, "cur": None, "nc": 1}

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
err = None
assert err is None
assert len(st["groups"]) == 3, f"grupos: {len(st['groups'])}"

cp, dp, rp = "C1-", "D1-", "R1-"
login_rows = g._rows_acceso()
curso_rows = g._rows_cursos(st, cp)
desc_rows = g._rows_descarga(dp)
totals = {"ok": 24, "skip_exist": 3, "filtered_format": 71, "error": 0}
st["selection"] = [{"name": "x"}]
st["errores"] = []
res_rows = g._rows_resumen(st, rp, totals)
print("layouts OK: acceso", len(login_rows), "cursos", len(curso_rows),
      "descarga", len(desc_rows), "resumen", len(res_rows))

# ventana real pero fuera de pantalla; no será visible para nadie
w = g._make_window()
w.finalize()
w.move(-30000, -30000)
st["body"] = w["-BODY-"]
assert "-STEP0-" in w.AllKeysDict and "-SESS-" in w.AllKeysDict
w.extend_layout(st["body"], [[sg.Column(login_rows, key="-Vacc-", visible=False)]])
w.extend_layout(st["body"], [[sg.Column(curso_rows, key="-Vcur-", visible=False)]])
w.extend_layout(st["body"], [[sg.Column(desc_rows, key="-Vdes-", visible=False)]])
w.extend_layout(st["body"], [[sg.Column(res_rows, key="-Vres-", visible=False)]])
w.finalize()
assert w["-Vcur-"] . widget is not None
w["-Vcur-"].update(visible=True)
g._set_steps(w, 1)
g._sync_counter(w, st, cp)
for kchip in ("-STEP0-", "-STEP1-", "-ST-", "-SESS-", f"{cp}SEL"):
    assert kchip in w.AllKeysDict, kchip
w.read(timeout=300)
w.close()
print("window OK — marco, pasos, chip y vista Cursos montados")
