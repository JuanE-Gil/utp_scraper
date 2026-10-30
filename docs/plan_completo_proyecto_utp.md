# UTP+class Downloader v3 — Plan completo (Fases 1 a 4)

**Fecha:** 29 de octubre de 2026
**Estado global:** Fase 1 casi cerrada · Fases 2, 3 y 4 por ejecutar
**Convención:** lo marcado como *(no verificado)* es una hipótesis que debe comprobarse antes de darse por cierta.

---

## Índice

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Hallazgos verificados](#2-hallazgos-verificados)
3. [Fase 1 — Revisión y verificación de APIs](#3-fase-1--revisión-y-verificación-de-apis)
4. [Fase 2 — Arquitectura de la GUI](#4-fase-2--arquitectura-de-la-gui)
5. [Fase 3 — Automatización segura de credenciales](#5-fase-3--automatización-segura-de-credenciales)
6. [Fase 4 — Listado de cursos y descarga desde la GUI](#6-fase-4--listado-de-cursos-y-descarga-desde-la-gui)
7. [Requisitos de seguridad y cumplimiento](#7-requisitos-de-seguridad-y-cumplimiento)
8. [Especificaciones técnicas](#8-especificaciones-técnicas)
9. [Criterios de éxito y métricas](#9-criterios-de-éxito-y-métricas)
10. [Usabilidad y accesibilidad](#10-usabilidad-y-accesibilidad)
11. [Decisiones (ADR) y registro de riesgos](#11-decisiones-adr-y-registro-de-riesgos)
12. [Orden de ejecución](#12-orden-de-ejecución)
13. [Archivos entregados](#13-archivos-entregados)

---

## 1. Resumen ejecutivo

**Estado.** La v3 tiene modularizadas las capas `api`, `downloader`, `core`, `ui_cli` y `main` (suite 13/13 antes de la Fase 1; Tasks 1 a 5 del plan SDD completas). Tras la Fase 1 se verificó contra la plataforma real cómo obtener la matrícula completa, y se añadió la agrupación por ciclo con 12 pruebas nuevas en verde. Faltan las capas `auth` y `ui_gui`, el contrato de eventos ampliado y la cancelación.

**Riesgos principales.**
1. Un fallo de red o una cancelación deja archivos parciales con tamaño > 0 que la idempotencia trata como completos.
2. Concurrencia entre Playwright y el bucle de eventos de una GUI.
3. Contenido de ciclos antiguos: se probó una sección por ciclo, no todas.
4. Decisiones abiertas: ADR-0004 y ADR-0006.

**Beneficios de la GUI.** Sin DevTools ni copiar IDs, selección visual de cursos por ciclo, progreso claro con cancelación, acceso a ciclos anteriores, todo dentro del alcance ético fijado (ADR-0002).

---

## 2. Hallazgos verificados

Verificados con dos sondas ejecutadas contra la plataforma real (`fase1_reporte.json`, `fase1b_reporte.json`).

| Hallazgo | Resultado |
|---|---|
| `/course/student/courses` | **No es el endpoint correcto.** 500 con y sin `academicPeriodId`; la causa documentada antes era errónea. |
| `GET /learning/student/{userId}/dashboard-courses` | Devuelve **toda la matrícula** (31 cursos, 5 ciclos) en una llamada, con `period`, `sectionId` y `courseId`. Hallazgo del usuario. |
| `GET /course/student/{userId}/academicperiods` | 6 períodos; solo aporta etiquetas legibles y cuál es el vigente. |
| ¿Basta `requests`? | **Sí.** Playwright solo se necesita para el login. |
| `/full` por ciclo | 200 en los 5 ciclos probados (una sección por ciclo; 8 a 162 contenidos). |
| Unión períodos ↔ cursos | Por la tupla `(period, acadCareer, module)`: 6 de 6, tuplas únicas. |
| Ciclo vigente | `2263` — "2026 - Ciclo 2 Agosto PREG (001)" (`type == CURRENT_PERIOD` y `period != "9999"`). |
| Período `9999` | Dos grupos distintos (`PRED/000` y `PRED/011`); nunca es el ciclo vigente aunque venga marcado `CURRENT_PERIOD`. |
| Campo de sección | `sectionId` (UUID). `sectionCode` es otro dato y no sirve en la URL. |
| Vida útil del token | 86 400 s (24 h). |
| Colisiones | 2 `courseId` repetidos entre secciones/ciclos; 0 homónimos dentro de un mismo ciclo. |

---

## 3. Fase 1 — Revisión y verificación de APIs

**Objetivo.** Revisar módulos, dependencias, APIs y puntos de extensión; resolver las incógnitas que bloqueaban el diseño.

### 3.1 Estructura actual (README, tal cual)

```
utp_scraper/          → paquete v3 (capas del INFORME §4)
  ├── api.py          → HTTP puro: headers + get_section_full          [✅]
  ├── downloader.py   → sanitize + extract_urls + download_file        [✅ testado]
  ├── core.py         → collect_jobs + run_jobs (contrato de eventos) [✅ testado]
  ├── ui_cli.py       → TUI rich.Live; consume eventos                 [✅]
  ├── main.py         → python -m utp_scraper (credenciales por env)   [✅]
  └── courses.py      → lista de cursos editable (placeholder Épica B)
```

### 3.2 Arquitectura objetivo (INFORME §4, tal cual)

```
utp_scraper/
├── auth        → Login SSO, captura de headers y resolución de período académico
├── api         → Llamadas HTTP puras: listado de cursos, estructura completa de un curso
├── downloader  → Extracción de URLs, filtro de dominio/extensión, descarga con idempotencia
├── core        → Orquestación (equivalente a process_course), estado del progreso, sin dependencia de una UI concreta
├── ui_cli      → Presentación actual en terminal (rich.Live)
├── ui_gui      → (futuro) presentación en interfaz gráfica de escritorio
└── main        → Punto de entrada: login → selección → descarga, delega la presentación
```

*Nota:* `core` ahora también contiene `group_courses_by_period` (lógica pura). Es una desviación menor de este diagrama que debe reflejarse en INFORME §4.

### 3.3 Hallazgos de código

| # | Hallazgo | Estado | Fase |
|---|---|---|---|
| 1 | `run_jobs` solo emite eventos *después* de cada descarga. No existen `course_started`, `file_started` ni `course_finished`; `main.py` pregunta por `"course_started"` pero nadie lo emite. | Pendiente | 2 |
| 2 | El handler `on_event` y la mutación de `UiState` viven en `main.py`; una GUI tendría que duplicarlos. | Pendiente | 2 |
| 3 | No hay mecanismo de cancelación en `run_jobs`. | Pendiente | 2 |
| 4 | La rama `FILE` de `collect_jobs` usa `metadata["url"]` sin validar contra `UTP_FILE_DOMAIN`; el filtro de dominio, garantía documentada, no se aplica a ese caso. | Pendiente (falta ver qué URLs devuelve la API) | 1 / 2 |
| 5 | Colisión de carpetas: la carpeta del curso usaba solo el nombre; "Ruta Laboral" (×3) y "Matemática II" (×2) colisionaban. | **Resuelto** (`<ciclo>/<curso>`, sufijo `classNumber` ante homónimos) | 1 |
| 6 | Anotación `-> str` de `download_file` devolvía en realidad una tupla. | **Resuelto** (`Tuple[str, str]`) | 1 |
| 7 | `app_it.py` no pertenece al proyecto (importa `itsim` y lee `main.py` para volcarlo a un archivo oculto). | Pendiente | 1 |
| 8 | El INFORME dice "sin implementación de código" pero el README y `progress.md` registran código implementado. | Pendiente | 1 |
| 9 | **Archivos parciales:** `download_file` escribe directamente en el destino; un corte de red o una cancelación deja un archivo con tamaño > 0 que la siguiente ejecución omite como `skip_exist`. La matriz de errores solo cubre el caso de tamaño 0. | Pendiente, **bloquea la cancelación** | 2 |

### 3.4 Entregado en la Fase 1

- `api.py`: `list_dashboard_courses(user_id, headers)` y `list_academic_periods(user_id, headers)`.
- `core.py`: `group_courses_by_period(courses, periods=None)` → `(grupos, excluidos)`.
  - Clave de grupo: `(period, acadCareer, module)`.
  - Orden: vigente → ciclos anteriores por código descendente → pseudo-período 9999 al final.
  - Registros normalizados sin datos de docentes (minimización de datos).
  - Carpeta única `<ciclo>/<curso>`; ante homónimos **todos** llevan sufijo, para que la carpeta no dependa del orden de la API.
  - Ítems sin `sectionId`/`courseId` válidos se excluyen (matriz §8); sin alias de respaldo (ADR-0005).
  - `collect_jobs(data, course_name, folder=None)`: parámetro opcional; sin él se comporta como antes.
  - Sin `periods`, etiqueta "Ciclo <código>" y vigente = mayor código regular: **heurística de respaldo, no verificada**.
- `downloader.py`: anotación corregida.
- `tests/test_periods.py`: 12 pruebas con datos sintéticos.
- ADR-0005 cerrado.

### 3.5 Pendiente para cerrar la Fase 1

1. Integrar los archivos entregados y ejecutar la **suite completa** del repo (solo se probaron las 12 pruebas nuevas).
2. Tasks 6 (parity check manual contra v2.2) y 7 (merge a `main`) del plan SDD de `progress.md`.
3. Hallazgo 4: añadir a la sonda un conteo de **hosts** (sin rutas) de las URLs `FILE`, o diferirlo a la Fase 2.
4. Hallazgos 7 y 8.
5. Ediciones de documentación:
   - INFORME §2 y §11.3: el endpoint correcto es `dashboard-courses`; el 500 no se debía a `academicPeriodId`; los ciclos anteriores vienen en `dashboard-courses`.
   - ADR-0003: sustituir "el historial de `academicPeriods` queda disponible" por "los ciclos anteriores vienen en `dashboard-courses`; `academicPeriods` solo aporta etiquetas y cuál es el vigente".
   - `docs/adr/README.md`: marcar 0005 como "Cerrada (adoptada)".
   - `resumen-auth-demo.md`: **no tocar** (congelado); la corrección va en el INFORME.

**Criterio de salida:** suite completa verde con los cambios integrados, Tasks 6 y 7 hechas, documentación corregida y hallazgo 4 resuelto o explícitamente diferido.

---

## 4. Fase 2 — Arquitectura de la GUI

**Objetivo.** Dejar `core` listo para cualquier presentación (TUI o GUI) y decidir el framework, sin escribir aún pantallas.

### 4.1 Contrato de eventos ampliado

`core` no importa `rich` ni ninguna librería GUI; notifica por eventos.

| Evento | Estado | Datos |
|---|---|---|
| `course_started` | nuevo | curso, total de jobs |
| `file_started` | nuevo | semana, título, nombre de archivo |
| `downloaded` | existente | semana, título, nombre de archivo |
| `skipped_existing` | existente | semana, título, nombre de archivo |
| `error` | existente | semana, título, nombre de archivo, detalle |
| `filtered_format` | existente | semana, título, extensión |
| `course_finished` | nuevo | conteos |
| `cancelled` | nuevo | conteos parciales |

**Cuidado con el progreso:** hoy `main.py` incrementa `course_done` con todo evento salvo `course_started`. Con los eventos nuevos, solo los eventos *terminales* de archivo (`downloaded`, `skipped_existing`, `error`, `filtered_format`) deben avanzar el contador; `file_started` y `course_started` no.

### 4.2 Tareas

| # | Tarea | Detalle |
|---|---|---|
| 2.1 | Ampliar el contrato de eventos | Con pruebas unitarias que usen un `download_file` falso (sin red). |
| 2.2 | Mover el handler a `ui_cli` | `make_handler` y la mutación de `UiState` salen de `main.py`; `main` solo orquesta. |
| 2.3 | **Descarga atómica** (hallazgo 9) | Escribir en `<archivo>.part` y renombrar al terminar bien; al iniciar, un `.part` huérfano se descarta. Debe estar **antes** del botón Cancelar, porque cancelar generará parciales. Prueba: corte simulado a mitad de un archivo → la siguiente ejecución lo vuelve a descargar. |
| 2.4 | Cancelación | `run_jobs(jobs, root_dir, on_event, cancel=None)` con un `threading.Event`; se comprueba entre archivos y dentro del bucle de `chunks`; emite `cancelled`. |
| 2.5 | Validar dominio en la rama `FILE` | Según lo que muestre el conteo de hosts (hallazgo 4). |
| 2.6 | Cerrar ADR-0006 (framework) | Ver 4.3. |
| 2.7 | Validar el mockup §12.2 | Contra los flujos de las Épicas A y B (criterio de cierre del ADR-0006). |
| 2.8 | Definir la concurrencia | Ver 4.4. |

### 4.3 Selección del framework (ADR-0006)

| Opción | A favor | En contra |
|---|---|---|
| FreeSimpleGUI | Ligera, curva baja, suficiente para 3 pantallas | Menos control visual y de accesibilidad |
| PySide6 (Qt) | Hilos y señales nativos, mejor accesibilidad y aspecto | Más peso y complejidad |

Recomendación inicial: **FreeSimpleGUI** para las tres pantallas mínimas; si la accesibilidad pasa a ser prioridad, el contrato de eventos permite migrar a PySide6 sin tocar `core`. Es una recomendación, no una decisión cerrada.

*(No verificado)* El ADR-0006 describe FreeSimpleGUI como MIT; hay que **confirmar la licencia vigente** del paquete antes de adoptarlo.

### 4.4 Concurrencia

- La descarga corre en un **hilo de trabajo** y comunica a la GUI por una `queue.Queue` de eventos; la GUI consulta la cola desde su propio bucle y nunca se bloquea.
- El login con Playwright (`sync_api`) se ejecuta en un **hilo o subproceso propio**, nunca en el hilo de la GUI. Si se usa un subproceso, la sesión debe volver por un canal en memoria (tubería), **no** por argumentos de línea de comandos, variables de entorno ni disco.
- La cancelación se propaga con el `threading.Event` de 2.4.

### 4.5 Ubicación de módulos

`auth` (nuevo, Fase 3) · `api` (ampliado) · `core` (eventos, cancelación, agrupación) · `ui_cli` (recibe el handler) · `ui_gui` (nuevo, Fase 4) · `main` (solo orquesta).

**Criterio de salida:** eventos nuevos con pruebas, descarga atómica con prueba de corte, cancelación funcionando, ADR-0006 cerrado con fecha, mockup validado.

---

## 5. Fase 3 — Automatización segura de credenciales

**Objetivo.** Un módulo `auth` que inicie sesión sin intervención manual y entregue una sesión **solo en memoria**.

### 5.1 Diseño

- `auth.login(codigo, contrasena) → Session` (dataclass en memoria): `auth_token`, `user_id`, `tenant_id`, `expires_at`.
- `expires_at` se calcula del JWT (`iat` + 86 400 s, verificado); solo se decodifica el *payload* para leer tiempos, nunca se muestra.
- La contraseña se pasa una vez al formulario SSO y se descarta; **no** forma parte de `Session`, de su `repr` ni de ningún log.
- El navegador se **cierra en cuanto se capturan los headers**: la Fase 1 demostró que `requests` basta para el resto.
- Espera del dashboard con `domcontentloaded` + `text=Actividades semanales`; nunca `networkidle` (resuelto en el desarrollo previo).
- Selectores genéricos de login y manejo explícito de `#idSIButton9`, ya probados en las demos.

### 5.2 Máquina de estados (INFORME §10.1, tal cual)

```
INICIO → CARGANDO_SSO → ESPERANDO_USUARIO → ESPERANDO_CLAVE
   → CONFIRMANDO_SESION? → CARGANDO_DASHBOARD
   → CAPTURANDO_TOKENS → RESOLVIENDO_PERIODO → LISTO_PARA_SELECCION

Salidas de error posibles desde cualquier estado:
   → ERROR_TIMEOUT | ERROR_CREDENCIALES | ERROR_TOKEN_NO_CAPTURADO | ERROR_PERIODO_NO_ENCONTRADO
```

Ajuste propuesto: con el hallazgo de `dashboard-courses`, `RESOLVIENDO_PERIODO` deja de ser bloqueante para listar cursos (solo aporta etiquetas). Un fallo de `academicperiods` no debe abortar el flujo: se usa la etiqueta de respaldo. Se añade `ERROR_SESION_EXPIRADA` (401 durante el uso).

### 5.3 Tareas

| # | Tarea | Detalle |
|---|---|---|
| 3.1 | Módulo `auth` con errores tipados | Cada salida de error de la máquina de estados es una excepción propia que la GUI traduce a un mensaje. |
| 3.2 | Captura de headers robusta | Aborta con `ERROR_TOKEN_NO_CAPTURADO` si no llegan `authorization` y `user-id`. |
| 3.3 | Detección de credenciales inválidas | `ERROR_CREDENCIALES` es **terminal y sin reintento** (ADR-0001, prueba A-02). *(No verificado)* No se conoce el selector del mensaje de error del SSO. **No probar con una contraseña incorrecta deliberadamente** (riesgo de bloqueo de la cuenta institucional). Heurística propuesta: tras enviar la contraseña, si la página sigue en el SSO con el campo de contraseña visible al vencer el tiempo, se clasifica como credenciales inválidas. |
| 3.4 | Ciclo de vida del token | La GUI avisa cerca de `expires_at`; ante un 401 vuelve al login y conserva lo ya descargado (la idempotencia lo permite, una vez resuelto el hallazgo 9). |
| 3.5 | Modo headless | *(No verificado)* Las demos usan `headless=False`. Probar si el SSO funciona sin ventana; hasta comprobarlo, mantener ventana visible. |
| 3.6 | MFA o captcha | *(No verificado)* Las demos solo muestran el aviso "¿Mantener sesión iniciada?". Si aparece otro paso, se clasifica como `ERROR_TIMEOUT` con un mensaje claro. |
| 3.7 | Requisito de Playwright | La GUI comprueba que Chromium está instalado (`playwright install chromium`) y, si falta, muestra una instrucción clara en vez de un error técnico. |
| 3.8 | Política de logs | Helper de redacción: ningún valor de `authorization`, `user-id` ni `x-tenant-id` llega a logs, mensajes de error ni capturas. Sin `screenshot` de login. |
| 3.9 | Persistencia opcional (post-MVP) | "Recordar sesión" con `keyring`, **desactivada por defecto** y solo para el token (nunca la contraseña). Dado que el token dura 24 h, el beneficio es bajo: se recomienda no implementarla en la primera versión. |

### 5.4 Pruebas

- Unitarias con un Playwright simulado: transiciones de estado, errores tipados, cálculo de `expires_at`, y que ni la contraseña ni el token aparezcan en `repr(Session)` ni en logs.
- Manuales: A-01 a A-04 del INFORME §9 (login exitoso, contraseña incorrecta **sin** reintento automático, popup ausente, red interrumpida).

**Criterio de salida:** login automático ≥ 95 % de éxito en pruebas manuales repetidas con red estable, auditoría confirma 0 apariciones de contraseña/token en disco o logs.

---

## 6. Fase 4 — Listado de cursos y descarga desde la GUI

**Objetivo.** Conectar la sesión, el listado agrupado y la descarga en las tres pantallas, incluyendo ciclos anteriores.

### 6.1 Flujo de datos

1. `auth.login` → `Session` (en memoria).
2. `api.list_dashboard_courses(user_id, headers)` y `api.list_academic_periods(user_id, headers)` (esta última opcional).
3. `core.group_courses_by_period(courses, periods)` → `(grupos, excluidos)`.
4. La GUI muestra los grupos; el usuario selecciona cursos.
5. Por cada curso: `api.get_section_full(course_id, section_id, headers)` → `core.collect_jobs(data, name, folder=registro["folder"])` → `core.run_jobs(..., on_event, cancel)` en el hilo de trabajo.

La lista proviene **solo** de la matrícula del usuario autenticado; nunca de un `sectionId` ingresado a mano (ADR-0002, B4, alcance protegido de `AGENTS.md`).

### 6.2 Tareas

| # | Tarea | Detalle |
|---|---|---|
| 4.1 | Pantalla de selección agrupada | Ciclo vigente expandido; "Ciclos anteriores" plegado; "Otros (sin ciclo)" plegado (grupo 9999, antes se filtraba). Casillas por curso y "seleccionar todo" por grupo. Opción "Cancelar" (B3). |
| 4.2 | Ciclos anteriores (B5) | Ya vienen en la misma respuesta; no requiere llamadas adicionales. |
| 4.3 | Manejo de errores por curso | **403/404 en `/full`** → el curso se marca "contenido no disponible" y se continúa con el siguiente (se probó una sección por ciclo, no todas). **401** → volver al login. **Lista vacía** → "No tienes cursos matriculados". **Excluidos** (sin `sectionId`/`courseId`) → aviso en el registro. **`academicperiods` falla** → etiqueta de respaldo. |
| 4.4 | Botón "Actualizar" | Repite la consulta con el token vigente; si expira, vuelve al login. |
| 4.5 | Pantalla de progreso | Curso actual, barra, archivo en curso (`file_started`), contadores, botón Cancelar siempre disponible, resumen final. |
| 4.6 | Paridad en CLI | `main.py` usa el mismo flujo; selección por texto (`"1"`, `"1,3"`, `"todos"`, `0` = cancelar; máximo 3 intentos, matriz §8). |
| 4.7 | Cerrar ADR-0004 | La GUI usa casillas nativas, así que la duda del checklist en terminales embebidas solo afecta a la CLI. Propuesta: mantener el prompt de texto en la CLI y cerrar el ADR con esa decisión. Decisión pendiente del usuario. |
| 4.8 | Verificación ampliada (opcional) | Modo de comprobación que haga `GET /full` de **todas** las secciones elegidas y reporte accesibilidad, para sustituir la muestra de una por ciclo. |

### 6.3 Propuesta de pantalla de selección (nueva; a validar)

```
┌─ Cursos ──────────────────────────────────────────┐
│ ▼ 2026 - Ciclo 2 Agosto PREG (001)     [vigente]  │
│     ☐ Mecánica Clásica                            │
│     ☐ Cálculo I                                   │
│     ...                                           │
│ ▶ Ciclos anteriores (3)                           │
│ ▶ Otros (sin ciclo) (2)                           │
│                         [Descargar seleccionados] │
└───────────────────────────────────────────────────┘
```

### 6.4 Pruebas

Bloques B y C del INFORME §9, más: ciclo anterior sin contenido (403/404), token expirado a mitad de descarga, lista con elementos excluidos, y comprobación de que ninguna sección fuera de la matrícula puede seleccionarse.

**Criterio de salida:** la lista de la GUI coincide al 100 % con la de la plataforma (ciclo vigente y al menos uno anterior), 0 cursos sin `sectionId` válido ofrecidos, regresión C-01 a C-03 sin cambios.

---

## 7. Requisitos de seguridad y cumplimiento

| Requisito | Detalle |
|---|---|
| Contraseña | Solo en memoria, durante el login; sin logs ni autofill; no forma parte de la sesión (ADR-0001). |
| Token e IDs | Solo en memoria; vida ≈ 24 h. La persistencia es opcional, explícita y delegada en el almacén del sistema operativo (`keyring`); no se inventa cifrado propio. |
| Mínimo privilegio | Un solo rol (`STUDENT`). Ninguna sección fuera de la matrícula (ADR-0002). |
| Minimización de datos | Los registros de curso no llevan correos ni datos de docentes. |
| Logs y auditoría | Se registran eventos (curso, archivo, resultado) sin valores de credenciales; nunca fragmentos del token en pantalla. |
| Capturas de error | Sin capturas de pantalla del login; si se usan para diagnóstico, no se versionan y se borran después. |
| Descargas | Escritura atómica (`.part`) para que un corte no deje archivos corruptos como válidos. |
| `.gitignore` | `dist/`, `node_modules/`, `.venv/`, `descargas_utp/`, `fase1_reporte.json`, `fase1b_reporte.json`, capturas y evidencias (AGENTS.md). |
| Uso responsable | Uso personal, sin redistribución, respetando el reglamento de la plataforma; mantener la pausa entre descargas (`time.sleep(0.1)`). |
| **Diferido por decisión del usuario** | Saneamiento de credenciales y revisión del historial git antes de publicar el repositorio (`utp_scraper_v2.2.py` y el anexo del informe contienen valores reales). Se retomará antes de cualquier publicación. |

---

## 8. Especificaciones técnicas

### 8.1 Flujo de usuario en la GUI (wireframes INFORME §12.2, tal cual)

```
[Pantalla 1: Login]              [Pantalla 2: Selección]         [Pantalla 3: Progreso]
 ┌────────────────┐               ┌────────────────────┐         ┌──────────────────────┐
 │ Usuario  [___]  │               │ ☐ Mecánica Clásica  │         │ Curso: Mecánica Clás. │
 │ Clave    [___]  │   ───────►    │ ☐ Cálculo III       │  ────►  │ ████████░░░  62%      │
 │ [Iniciar sesión]│               │ ☐ Prog. Avanzada    │         │ Archivo: guia_03.pdf  │
 └────────────────┘               │   [Descargar seleccion.]│     │ ✅ 24  ⏭ 3  ❌ 0       │
                                    └────────────────────┘         └──────────────────────┘
```

Secuencia: Login (usuario y clave enmascarada) → estados de la máquina de §5.2 con indicador de progreso → Selección (vigente por defecto, "Ciclos anteriores" plegado, casillas múltiples, "Cancelar") → Progreso (con cancelación) → resumen final.

### 8.2 Interacción entre la GUI y la lógica modular

| De | A | Mecanismo |
|---|---|---|
| `ui_gui` | `auth` | Llamada en hilo/subproceso; recibe `Session` o un error tipado |
| `ui_gui` | `api` | `list_dashboard_courses`, `list_academic_periods` |
| `ui_gui` | `core` | `group_courses_by_period`; `collect_jobs` + `run_jobs(jobs, root_dir, on_event, cancel)` en hilo de trabajo |
| `core` | `ui_gui` | Cola de eventos consumida por el bucle de la GUI |
| `core` | `downloader` | Idempotencia y filtros; escritura atómica `.part` |

### 8.3 Extracción de credenciales

`auth` abre Chromium, completa el SSO, intercepta los headers `authorization`, `user-id` y `x-tenant-id` de las peticiones a `api-pao.utpxpedition.com`, cierra el navegador y devuelve la `Session`. No devuelve la contraseña.

### 8.4 Recuperación de cursos

`GET /learning/student/{userId}/dashboard-courses` devuelve la matrícula completa; se agrupa por `(period, acadCareer, module)`. `GET /course/student/{userId}/academicperiods` aporta etiquetas y el ciclo vigente. Ambas funcionan con `requests` y los mismos headers que `get_section_full`.

---

## 9. Criterios de éxito y métricas

Los umbrales son **propuestas iniciales** a calibrar con datos reales; no hay línea base medida.

| Área | Métrica | Meta propuesta |
|---|---|---|
| Autenticación | Login completo sin intervención, red estable | ≥ 95 % en pruebas manuales repetidas |
| Credenciales | Hallazgos de contraseña o token en disco, logs o repositorio | 0 |
| Cursos | Coincidencia lista GUI vs. plataforma (vigente y ≥ 1 anterior) | 100 % |
| Exclusión | Cursos sin `sectionId` válido ofrecidos para selección | 0 |
| Integridad | Archivos parciales tratados como completos tras un corte o cancelación | 0 |
| Descarga | Regresión C-01 a C-03 y suite completa | Sin regresiones |
| Rendimiento | Tiempo de login → lista de cursos | Medir y fijar objetivo tras la Fase 3 |
| Responsividad | La GUI no se congela durante login ni descarga | Verificado manualmente |
| Resiliencia | Token expirado sin pérdida de lo descargado | Verificado |
| Documentación | ADR-0004 y ADR-0006 cerrados con fecha | 2/2 (0005 ya cerrado) |

---

## 10. Usabilidad y accesibilidad

- **Consistencia:** mismos términos que la TUI ("Descargados", "Ya existían", "Filtrados por formato", "Errores") y mismos iconos de estado (✅ ⏭ 🚫 ❌), siempre acompañados de texto, nunca solo color o icono.
- **Mensajes de error claros y accionables**, por ejemplo:
  - Credenciales inválidas: "Código o contraseña incorrectos. No se reintentará automáticamente para evitar bloquear tu cuenta."
  - Sin cursos: "No tienes cursos matriculados este período."
  - Token expirado: "Tu sesión expiró. Inicia sesión de nuevo; lo ya descargado se conserva."
  - Curso sin contenido: "El contenido de este curso ya no está disponible en la plataforma."
  - Chromium ausente: "Falta el navegador de automatización. Ejecuta `playwright install chromium`."
- **Accesibilidad:** navegación completa por teclado, orden de tabulación lógico, contraste suficiente, tamaños de fuente ajustables, etiquetas explícitas en los campos y progreso también como texto.
- **Seguridad en la interfaz:** campo de clave enmascarado, el token nunca se muestra, botón "Cancelar" siempre disponible durante descargas.
- **Ayuda mínima:** un texto breve en el Login que explique que la contraseña no se guarda y que solo se accede a los cursos del propio usuario.
- **Validación:** probar los mockups contra los flujos de las Épicas A y B antes de implementar.

---

## 11. Decisiones (ADR) y registro de riesgos

### 11.1 Estado de los ADR

| ADR | Título | Estado | Acción |
|---|---|---|---|
| 0001 | No reintentar login con credenciales inválidas | Cerrada | Se respeta en la Fase 3 |
| 0002 | Secciones restringidas a la matrícula | Cerrada | La lista proviene solo de `dashboard-courses` |
| 0003 | Períodos anteriores como opción explícita | Cerrada | Actualizar su consecuencia (ver 3.5) |
| 0004 | Checklist vs. prompt de texto | **Abierta** | Cerrar en la Fase 4 (propuesta en 6.2, tarea 4.7) |
| 0005 | `sectionId` como fuente única | **Cerrada** (29 oct 2026) | Hecho |
| 0006 | Framework de GUI | **Abierta** | Cerrar en la Fase 2 |

### 11.2 Registro de riesgos

| Riesgo | Impacto | Mitigación | Fase |
|---|---|---|---|
| Archivos parciales tratados como completos | Material corrupto silencioso | Escritura atómica `.part` | 2 |
| Playwright y el bucle de la GUI en conflicto | Congelamiento o errores | Hilo o subproceso propio, cola de eventos | 2 |
| Contenido antiguo no disponible en algún curso | Descarga incompleta | Manejo de 403/404 por curso; modo de verificación ampliada | 4 |
| SSO con MFA o captcha *(no verificado)* | Login no automatizable | Clasificar como `ERROR_TIMEOUT` con mensaje claro | 3 |
| Detección de "credenciales inválidas" sin selector conocido | Mensaje incorrecto | Heurística; sin pruebas con contraseña incorrecta | 3 |
| Licencia de FreeSimpleGUI *(no verificado)* | Incompatibilidad de uso | Confirmar antes de adoptar | 2 |
| Cambios en la API de UTP | Rotura del listado | Pruebas con respuestas simuladas; sondas reutilizables | Todas |
| `academicperiods` no disponible | Etiquetas genéricas | Etiqueta y vigente de respaldo (heurística) | 4 |

---

## 12. Orden de ejecución

```
Fase 1 (cerrar)  →  Fase 2  →  Fase 3  →  Fase 4
```

| Paso | Contenido | Depende de |
|---|---|---|
| 1 | Cerrar la Fase 1 (suite completa, Tasks 6 y 7, hallazgo 4, documentación) | — |
| 2 | Contrato de eventos + handler a `ui_cli` (2.1, 2.2) | 1 |
| 3 | Descarga atómica y cancelación (2.3, 2.4) | 2 |
| 4 | ADR-0006 y validación del mockup (2.6, 2.7) | 2 |
| 5 | Módulo `auth` (Fase 3 completa) | 3, 4 |
| 6 | Pantallas y flujo completo (Fase 4) | 5 |
| 7 | Cierre de ADR-0004, consolidación documental y actualización del INFORME y el Kanban | 6 |

Se recomienda empezar por el **contrato de eventos** (paso 2), porque desbloquea tanto la GUI como el botón de cancelar.

---

## 13. Archivos entregados

| Ruta | Descripción |
|---|---|
| `tools/probe_fase1.py` | Sonda 1: endpoints y forma de las respuestas |
| `tools/probe_fase1b.py` | Sonda 1b: `requests`, unión de períodos, `/full` por ciclo |
| `utp_scraper/api.py` | Nuevas llamadas de matrícula y períodos |
| `utp_scraper/core.py` | Agrupación por ciclo y carpetas sin colisión |
| `utp_scraper/downloader.py` | Anotación de retorno corregida |
| `tests/test_periods.py` | 12 pruebas nuevas |
| `docs/adr/0005-unificar-sectionId.md` | ADR cerrado |
