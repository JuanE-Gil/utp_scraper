# UTP+class Downloader v3 — Estado tras la Fase 1 y siguientes pasos

**Fecha:** 29 de octubre de 2026

---

## 1. Qué se ha hecho

### Análisis y plan
- Análisis del estado del proyecto modularizado y plan de implementación en 4 fases (Fase 1: revisión de módulos y APIs; Fase 2: arquitectura de la GUI; Fase 3: credenciales; Fase 4: listado de cursos).

### Verificación contra la plataforma real
Se escribieron dos sondas (`probe_fase1.py` y `probe_fase1b.py`) que se ejecutaron contra UTP+class. Resultados:

| Hallazgo | Resultado |
|---|---|
| Endpoint `/course/student/courses` | **No es el correcto.** Responde 500 con y sin `academicPeriodId`. La causa documentada antes (falta del parámetro) era errónea. |
| Endpoint `dashboard-courses` | Hallazgo del usuario. `GET /learning/student/{userId}/dashboard-courses` devuelve **toda la matrícula** (31 cursos, 5 ciclos) en una llamada, con `period`, `sectionId` y `courseId`. |
| ¿Basta `requests`? | **Sí.** `dashboard-courses` y `academicperiods` dieron 200 sin navegador. Playwright solo se necesita para el login. |
| ¿Ciclos anteriores accesibles? | **Sí.** `/full` devolvió 200 en los 5 ciclos probados (una sección por ciclo). |
| ¿Se unen períodos y cursos? | **Sí.** Las 6 tuplas `(period, acadCareer, module)` coinciden 1:1 con los 6 items de `academicperiods`. |
| Ciclo vigente | `2263` — "2026 - Ciclo 2 Agosto PREG (001)". |
| Período `9999` | Contiene **dos grupos** (`PRED/000` y `PRED/011`); nunca cuenta como ciclo vigente. |
| Duración del token | 86 400 s (24 h), confirmado. |
| Colisiones | 2 `courseId` aparecen en varias secciones/ciclos (ej. "Ruta Laboral" ×3, "Matemática II" ×2). No hay homónimos dentro de un mismo ciclo. |

### Código entregado (12 pruebas en verde)
- **`utp_scraper/api.py`:** nuevas `list_dashboard_courses` y `list_academic_periods`, ambas por `user-id`.
- **`utp_scraper/core.py`:** nueva `group_courses_by_period` (agrupa por tupla, ordena: vigente → ciclos anteriores por código descendente → 9999 al final; carpetas `<ciclo>/<curso>` sin colisiones; registros sin datos de docentes). `collect_jobs` acepta un `folder` opcional; sin él se comporta como antes.
- **`utp_scraper/downloader.py`:** anotación de `download_file` corregida a `Tuple[str, str]` (compatible con Python 3.8).
- **`tests/test_periods.py`:** 12 pruebas con datos sintéticos.
- **`docs/adr/0005-unificar-sectionId.md`:** ADR cerrado con la evidencia.

### Decisiones tomadas
- Identidad de una sección = `sectionId` (sin alias de respaldo; `sectionCode` es otro dato y no sirve en la URL).
- Clave de agrupación = `(period, acadCareer, module)`, no `period` solo.
- Ante nombres repetidos dentro de un ciclo, **todos** los homónimos llevan sufijo (`classNumber`), para que la carpeta no dependa del orden de la API y se conserve la idempotencia.

---

## 2. Pendiente de la Fase 1

1. **Integrar los archivos en el repo y ejecutar la suite completa.** Solo se probaron las 12 pruebas nuevas; la suite existente no estaba disponible. Los cambios en `core.py` son aditivos, pero hay que confirmarlo.
2. **Aplicar las ediciones de documentación:**
   - INFORME §2 y §11.3: el endpoint correcto es `dashboard-courses`; el 500 no se debía a `academicPeriodId`; los ciclos anteriores vienen en `dashboard-courses`, no en la respuesta de períodos.
   - ADR-0003: sustituir "el historial de `academicPeriods` queda disponible" por "los ciclos anteriores vienen en `dashboard-courses`; `academicPeriods` solo aporta etiquetas y cuál es el vigente".
   - `docs/adr/README.md`: marcar 0005 como "Cerrada (adoptada)".
   - `resumen-auth-demo.md`: **no tocar** (documento congelado); la corrección va en el INFORME.
3. **Hallazgo 4: dominio en la rama `FILE` de `collect_jobs`.** Falta ver qué URLs devuelven realmente esos items. Opciones: añadir a la sonda un conteo de hosts (sin rutas) o diferirlo a la Fase 2.
4. **Detalles menores:**
   - Mantener `app_it.py` fuera del paquete (`archive/`), sin ejecutarlo ni incluirlo en `dist/`.
   - Corregir en el INFORME la frase "sin implementación de código", que ya no es cierta.

### Riesgos conocidos
- Se probó **una sección por ciclo**; un curso antiguo concreto podría fallar. La UI debe manejar 403/404 por curso.
- Si `academicperiods` falla, la etiqueta cae a "Ciclo 2263 (001)" y se marca como vigente el mayor código regular. Es una **heurística de respaldo, no un hecho verificado**.

---

## 3. Qué sigue

| Fase | Contenido |
|---|---|
| **Fase 2 — Arquitectura de la GUI** | Ampliar el contrato de eventos (`course_started`, `file_started`, `course_finished`, `cancelled`). Mover el handler de eventos de `main.py` a `ui_cli`. Añadir cancelación a `run_jobs` (`threading.Event`). Decidir el framework (ADR-0006; recomendación inicial: FreeSimpleGUI, pendiente de validar el mockup §12.2). Definir la concurrencia: descarga en hilo con cola de eventos y login de Playwright aislado. |
| **Fase 3 — Credenciales** | Módulo `auth` con la máquina de estados del login (INFORME §10.1). Sesión solo en memoria, navegador cerrado al capturar los headers, `keyring` como opción explícita y desactivada por defecto. `ERROR_CREDENCIALES` terminal, sin reintento (ADR-0001). |
| **Fase 4 — Cursos en la GUI** | Conectar el listado agrupado a la pantalla de selección, con "Ciclos anteriores" plegado y el grupo 9999 como "Otros (sin ciclo)". Manejo de 403/404 por curso, botón "Actualizar" y regreso al login si el token expira (401). Cerrar ADR-0004 (checklist o texto). |

### Recomendación de orden
Cerrar los puntos 1 a 3 de la Fase 1 y arrancar la Fase 2 por el **contrato de eventos**, porque desbloquea tanto la GUI como el botón de cancelar.

---

## 4. Archivos entregados

| Ruta | Descripción |
|---|---|
| `tools/probe_fase1.py` | Sonda 1: endpoints y forma de las respuestas |
| `tools/probe_fase1b.py` | Sonda 1b: `requests`, join de períodos, `/full` por ciclo |
| `utp_scraper/api.py` | Nuevas llamadas de matrícula y períodos |
| `utp_scraper/core.py` | Agrupación por ciclo y carpetas sin colisión |
| `utp_scraper/downloader.py` | Anotación de retorno corregida |
| `tests/test_periods.py` | 12 pruebas nuevas |
| `docs/adr/0005-unificar-sectionId.md` | ADR cerrado |