# UTP+class Downloader v3 — Resumen: login ROPC → GUI v1

**Fecha:** 30 de octubre de 2026
**Alcance:** todo lo implementado desde la verificación de ADR-0007 hasta la GUI v1 (inclusive).
**Estado al cierre:** suite **38/38** · `main` mergeada (tag `v3.1.0-alpha.1`) · trabajo nuevo en `feature/gui`.

---

## 1. Diagnóstico del login — navegador vs API (29-oct)

Pregunta abierta tras la sesión `dev-team`: ¿es necesario el navegador para
autenticarse, o bastan `requests`? Se zanjó con **sondas reales contra
producción** (credenciales solo por variables de entorno; nunca en código,
docs ni historial):

| # | Prueba | Resultado | Conclusión |
|---|---|---|---|
| 1 | ROPC con usuario ficticio | `invalid_grant` (401) | direct grant **habilitado** en `pao-web` (no `unauthorized_client`) |
| 2 | ROPC con credenciales reales | **200** + access (24 h) + refresh (~25 h) | login institucional **sin navegador** |
| 3 | Token en API, headers incompletos | 403 `explicit deny / identity-based policy` | el gateway valida más que el token |
| 4 | `user-id`/`x-tenant-id` reales, token crudo | 403 | faltaba algo más |
| 5 | Con `scope=openid` | 403 | el scope no era el bloqueo |
| 6 | `authorization: Bearer <token>` | **200 — 31 cursos** | **el prefijo Bearer es obligatorio** |
| 7 | `userinfo` de Keycloak | no trae el `user-id` de la API | no se "pide", se deriva |
| 8 | Source del SPA (`main.*.chunk.js`) | tenant hardcodeado; `user-id` derivado | **config cero** |

**Derivación verificada offline** (sin red):

```python
uuid.uuid5(uuid.NAMESPACE_DNS, "U21320952@UTP.EDU.PE")
# -> 04aba43a-d977-5c02-9dbb-cd97ed930438  (match exacto con el user-id real)
```

**Sondas reutilizables** (`tools/`, todo por env, nunca imprimen el token):
`probe_ropc_api.py` (login + derivación + 1 llamada) y `probe_compare.py`
(diff de claims web vs ROPC, para reaprobar si el proveedor cambia algo).

---

## 2. Documentación (un solo dueño por hecho)

- **`docs/adr/0007-login-ropc.md`** — decisión cerrada/adaptada con la
  evidencia: receta del POST (grant/client/scope), Bearer obligatorio,
  derivación de `user-id`, tenant constante, riesgo del proveedor cambiando
  el direct grant (detectable con la sonda). Índice ADR actualizado.
- **`docs/estado_proyecto_fase1.md`** — tabla de hallazgos actualizada.
- **Regla de credenciales (deliberación del usuario)**: AGENTS.md y README
  declaran secretos = solo `AUTH_TOKEN` y la contraseña. `USER_ID` (derivable)
  y `TENANT_ID` (constante pública del front) dejan de ser secretos.
- **Plan** (`docs/plan_completo_proyecto_utp.md` §4.2): Task **2.0** insertada
  (auth ROPC) y Task 2.1 registradas como hechas.

---

## 3. Task 2.0 — `utp_scraper/auth.py`

TDD: 4 tests con `requests` mockeado (RED confirmado → GREEN) + verificación
contra producción real (login → `dashboard-courses` 200, 31 cursos).

```python
login(username, password) -> Session   # 1 POST ROPC; AuthError tipado
refresh(refresh_token) -> Session      # renovación sin re-pedir clave (sesion > 24 h)
derive_user_id(email) -> str           # uuid5(NAMESPACE_DNS, email.upper())
Session.headers                        # Bearer + user-id derivado + tenant constante
```

Diseño defensivo: `login()` **jamás reintenta** (riesgo de bloqueo de cuenta,
regla del repo); el `email` viene dentro del JWT → cero entradas manuales;
la sesión vive solo en memoria.

---

## 4. Task 2.1 — contrato de eventos ampliado (TDD RED→GREEN→REFACTOR)

- **`core.run_jobs(jobs, root, on_event, course="")`** emite:
  `course_started(curso, total)` → `file_started(week, title, filename)` por
  intento → terminales → `course_finished(conteos)`. `cancelled` queda para
  la Task 2.4 (según plan §4.1).
- El `filename` de `file_started` replica la regla del downloader
  (basename del URL, fallback) para coherencia pre/post (tested).
- **`main.make_handler`** corrige el progreso: `course_done` solo avanza con
  `downloaded/skipped_existing/error/filtered_format` (antes contaba cualquier
  evento y duplicaría con los nuevos).
- Tests sin red (`download_file` falso por monkeypatch que replica la naming
  real): `tests/test_core_events.py` (5) + test del handler (1).

---

## 5. Git — merges y tag

```
feature/task-2.1-eventos --no-ff--> feature/gui --no-ff--> develop --no-ff--> main
tag: v3.1.0-alpha.1  ("Task 2.0 auth ROPC + Task 2.1 eventos; GUI pendiente")
```

Suite 38/38 verificada en cada rama antes de cada merge. Dep dev añadida:
`FreeSimpleGUI 5.1.0` (solo en `.venv`; el repo aún no tiene requirements.txt).

---

## 6. GUI v1 — `utp_scraper/ui_gui.py`

Tres pantallas conectadas por el **mismo contrato de eventos** (cero lógica de
descargas duplicada; consume solo `auth`/`api`/`core`, sin `rich`):

| Pantalla | Qué hace |
|---|---|
| **1 · Login** | usuario/clave en inputs (nunca en disco); `auth.login` con error en línea sin cerrar ventana |
| **2 · Selección** | matrícula agrupada por ciclo (`group_courses_by_period`); ciclo vigente pre-marcado; checkbox por curso; destino con `FolderBrowse` (default `descargas_utp`) |
| **3 · Progreso** | barra por curso (max = total de jobs), línea del archivo en vuelo, log de terminales, popup resumen final |

**Concurrencia (plan §4.4):** worker thread + `queue.Queue`; la GUI atiende
`read(timeout=25)` + `get_nowait` **en la misma iteración** para no congelar la
ventana (defecto detectado y corregido antes de commit). Botón **Cancelar
deshabilitado** (Task 2.4). Entrada: `python -m utp_scraper --gui` (el CLI
sin `--gui` sigue intacto).

---

## 7. Bugfixes tras prueba real (feedback del usuario)

| Problema | Causa | Fix |
|---|---|---|
| Crash en Selección: `TypeError ... argument 'default'` | `sg.Check(texto, default)` — el 2° posicional es `default`, yo pasaba `key` ahí | `key=` como kwarg, verificado contra la firma real (`05e61fd`) |
| Tamaño fijo, sin maximizar ni acoplar | ventanas sin `size`/`resizable` | `size=` + `resizable=True` en las 3 ventanas (habilita minimizar/maximizar y **Aero Snap** nativo); lista de cursos en `sg.Column(scrollable=True, vertical_scroll_only=True, expand_x/y)`; contenido adaptable con `expand_x/expand_y` (params verificados por `inspect`) (`a1c4ee8`) |

---

## 8. Estado del árbol al cierre

```
feature/gui (HEAD): a1c4ee8 resize -> 05e61fd fix Check -> 249d965 GUI v1 -> 81e0de6 merge Task 2.1
develop / main: en 81e0de6 (v3.1.0-alpha.1); GUI y fixes pendientes de merge
```

## 9. Pendiente

- Task 2.2: mover `make_handler` de `main.py` a `ui_cli.py` (`main` solo orquesta).
- Task 2.3: descarga atómica `.part` + rename (hallazgo 9).
- Task 2.4: cancelación real (`threading.Event` entre archivos y chunks) → habilita Cancelar; emite `cancelled(conteos parciales)`.
- Task 2.5: validar dominio en rama `FILE` de `collect_jobs` (hallazgo 4).
- Task 2.6/2.7: cerrar ADR-0006 (framework + empaquetado PyInstaller, mockup §12.2).
- Task 2.8: concurrencia GUI documentada en ADR.
