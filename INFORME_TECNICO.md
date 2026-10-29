# Informe Técnico — UTP+class Downloader v3

**Fase actual del proyecto:** Documentación, especificación y pruebas manuales (sin implementación de código).
**Metodología de gestión:** Scrum simplificado (proyecto personal, un solo rol PO/Dev/SM).
**Fecha del informe:** Septiembre 2026.

---

## Tabla de contenidos

1. [Contexto y objetivos](#1-contexto-y-objetivos)
2. [Diagnóstico del estado actual](#2-diagnóstico-del-estado-actual)
3. [Análisis de necesidad de datos](#3-análisis-de-necesidad-de-datos)
4. [Arquitectura objetivo (modular, preparada para GUI)](#4-arquitectura-objetivo-modular-preparada-para-gui)
5. [Metodología Scrum aplicada](#5-metodología-scrum-aplicada)
6. [Product Backlog](#6-product-backlog)
7. [Sprints](#7-sprints)
8. [Matriz de errores y casos borde](#8-matriz-de-errores-y-casos-borde)
9. [Plan de pruebas manuales](#9-plan-de-pruebas-manuales)
10. [Decision Log](#10-decision-log)
11. [Preguntas de diseño resueltas](#11-preguntas-de-diseño-resueltas)
12. [Mockups](#12-mockups)
13. [Tablero Kanban](#13-tablero-kanban)
14. [Checklist de cobertura de requisitos](#14-checklist-de-cobertura-de-requisitos)
15. [Consideraciones éticas y de seguridad](#15-consideraciones-éticas-y-de-seguridad)
16. [Próximos pasos](#16-próximos-pasos)

---

## 1. Contexto y objetivos

UTP+class es la plataforma de aprendizaje virtual de la Universidad Tecnológica del Perú. El proyecto nace de dos scripts previos desarrollados de forma independiente:

- Un **descargador de materiales** (`utp_scraper_v2.2.py`) que ya funciona de forma robusta contra la API interna (`api-pao.utpxpedition.com`), pero requiere que el usuario complete manualmente sus credenciales de sesión (`AUTH_TOKEN`, `USER_ID`, `TENANT_ID`) y la lista de cursos a descargar (`courseId`/`sectionId`).
- Una **demo de autenticación automática** (basada en Playwright) que resuelve el login vía SSO de Microsoft sin intervención manual, pero termina su ejecución al imprimir la lista de cursos, sin descargar nada.

### Visión del producto

> *"Una herramienta personal que, con un solo comando, inicie sesión en UTP+class, muestre los cursos disponibles, permita elegir cuáles descargar, y baje su contenido de forma completa, organizada y libre de duplicados o ruido — con una interfaz cómoda e intuitiva, primero en terminal (TUI) y luego en escritorio (GUI)."*

### Requisitos declarados del proyecto

1. **Login automático** — completo (ya resuelto en la demo de autenticación).
2. **Descarga automática del contenido** — completa a medias: falta automatizar la obtención y selección de cursos (hoy se ingresan a mano).
3. **Preparación para migración a una interfaz gráfica**, manteniéndose en Python.
4. **Documentación completa del proyecto**: fases, metodología (Kanban → evolucionado a Scrum con sprints en este informe), backlog, pruebas y decisiones.

---

## 2. Diagnóstico del estado actual

| Componente | Qué hace bien | Qué le falta |
|---|---|---|
| Motor de descarga (`utp_scraper_v2.2.py`) | Recorre unidades → temas → contenidos; filtra por dominio S3 (`utp-prd-upload-file-storage.s3.amazonaws.com`) y por extensión (lista blanca `DOWNLOAD_EXTENSIONS`); evita duplicados (idempotencia por tamaño > 0); TUI en tiempo real con `rich.Live` | Credenciales y lista de cursos hardcodeadas manualmente en el código |
| Demo de autenticación (Playwright) | Login automático, bypass de SSO Microsoft (`domcontentloaded` + espera de `"Actividades semanales"` en vez de `networkidle`), captura de headers en tiempo real, resolución del período académico vigente, fetch nativo de cursos dentro del navegador autenticado | No selecciona cursos ni descarga contenido; el flujo termina al mostrar la tabla/JSON de cursos |

**Conclusión del diagnóstico:** no falta tecnología nueva. Falta el **"pegamento"** entre ambas piezas: usar la salida de la autenticación (tokens + lista de cursos) como entrada de la fase de descarga, agregando un paso intermedio de selección por parte del usuario.

### Incidencias ya resueltas (heredadas del desarrollo previo)

| Incidencia | Causa raíz | Solución adoptada |
|---|---|---|
| Timeout esperando `"text=Mis cursos"` | El SPA de UTP+class no termina de renderizar tras la redirección del SSO antes de que se busque el selector | Selectores genéricos de login + manejo explícito del botón `#idSIButton9` |
| Bloqueo indefinido con `networkidle` | Banners, carruseles y polling de analítica impiden que la red llegue a reposo absoluto | Uso de `wait_until="domcontentloaded"` + espera de un nodo estable (`"text=Actividades semanales"`) |
| Datos hardcodeados en las tablas | Simulación visual desacoplada de la extracción real | Intercepción pasiva de red (`page.on("response", ...)`) |
| Error 500 al consultar la API externa | Falta el parámetro `academicPeriodId` y headers de contexto (`x-tenant-id`, `user-id`, `user-role`) | `fetch` nativo inyectado con `page.evaluate()`, dentro del contexto autenticado del navegador |
| Captura de payloads irrelevantes (conteo de notificaciones, etc.) | La SPA dispara múltiples peticiones simultáneas al cargar | Filtrado explícito por `type == "CURRENT_PERIOD"` y validación de claves (`name`, `courseName`, `sectionId`) antes de aceptar una respuesta como "lista de cursos" |

---

## 3. Análisis de necesidad de datos

Antes de construir nada, se audita cada dato capturado por el sistema para no arrastrar dependencias innecesarias.

| Dato | ¿Necesario? | Justificación |
|---|---|---|
| `AUTH_TOKEN` (Bearer JWT) | **Sí, imprescindible** | Toda petición a la API lo exige; sin él, 401. |
| `USER_ID` | **Sí, imprescindible** | La API es multiusuario; el backend resuelve con este header a quién pertenecen los datos. |
| `TENANT_ID` | **Sí, imprescindible** | Plataforma multi-institución (multi-tenant); sin este header la API no identifica la organización. |
| `academicPeriodId` | **Sí, imprescindible** | La API de cursos responde error 500 sin este parámetro. Además, sin filtrar por período, un usuario con varios ciclos cursados tendría un listado ambiguo entre cursos vigentes y pasados. |
| `courseId` | **Sí** | Identifica el recurso raíz del curso; sin él no hay endpoint que consultar. |
| `sectionId` | **Sí** | Un mismo curso puede tener varias secciones (paralelos); el contenido depende de la sección específica del usuario. |
| Contraseña del usuario | **Necesaria solo en el instante del login, nunca almacenada** | Se usa una vez para completar el formulario SSO; no debe persistir en ningún archivo ni log. |
| Historial completo de `academicPeriods` (no solo el actual) | **No necesario por defecto**, pero disponible sin trabajo adicional | Ya viaja en la misma respuesta que hoy se filtra a un solo período — ver §11.3 para su uso opcional. |
| Conteo de notificaciones/mensajes | **No, es ruido** | Payload irrelevante ya identificado y descartado. |

**Conclusión:** los datos que hoy se capturan son, en su totalidad, necesarios. El problema del proyecto nunca fue de exceso de datos, sino de **integración**: conectar automáticamente lo que la autenticación ya obtiene con lo que la descarga ya sabe usar.

---

## 4. Arquitectura objetivo (modular, preparada para GUI)

Para poder envolver la lógica actual en una interfaz gráfica sin reescribirla, se especifica (sin implementar aún) una separación en capas:

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

**Principio de diseño central:** el módulo `core` no debe invocar directamente una librería de presentación (como `rich`). En su lugar, debe notificar el progreso mediante un **contrato de eventos** (p. ej. "archivo descargado", "curso iniciado", "error en archivo X"), que cada capa de presentación interpreta a su manera — una tabla en terminal, o una barra de progreso en una ventana. Este contrato se define en prosa en este informe y se detalla en el Sprint 4 (§7).

---

## 5. Metodología Scrum aplicada

Proyecto pequeño y personal → Scrum simplificado: un solo Product Owner/Developer/Scrum Master, sprints cortos, ceremonias reducidas a **Planning + Review + Retro documentados** (sin daily formal).

### Definition of Ready (DoR)

Una historia puede entrar a un sprint si:
- Tiene criterios de aceptación claros.
- Se identificaron sus posibles errores/casos borde.
- No depende de una historia que sigue en curso.

### Definition of Done (DoD)

Una historia se cierra si:
- Cumple todos sus criterios de aceptación.
- Sus casos de error están documentados y probados manualmente (o el mockup fue validado visualmente).
- Quedó reflejada en la documentación del proyecto.
- No introdujo un dato o dependencia sin justificar (ver §3).

---

## 6. Product Backlog

Prioridad MoSCoW: **M**ust / **S**hould / **C**ould / **W**on't.

### Épica A — Autenticación unificada

| ID | Historia | Prioridad | Criterios de aceptación |
|---|---|---|---|
| A1 | Como usuario, quiero iniciar sesión sin intervención manual salvo mis credenciales | M | Login completa sin timeouts; captura `AUTH_TOKEN`, `USER_ID`, `TENANT_ID` de forma confiable con red estable |
| A2 | Como usuario, quiero que el sistema obtenga el período académico vigente automáticamente | M | Se identifica `type=CURRENT_PERIOD` y `period≠"9999"` sin intervención |
| A3 | Como usuario, quiero que mi contraseña nunca quede en disco ni en logs | M | Auditoría manual confirma que no aparece en ningún archivo generado |

### Épica B — Descubrimiento y selección de cursos

| ID | Historia | Prioridad | Criterios de aceptación |
|---|---|---|---|
| B1 | Como usuario, quiero ver la lista de mis cursos del período actual tras el login | M | Tabla con nombre, courseId, sectionId; cero cursos hardcodeados |
| B2 | Como usuario, quiero elegir uno, varios, o todos los cursos a descargar | M | Acepta índice único, lista separada por comas, "todos"; rechaza entradas inválidas con mensaje claro. El mecanismo de selección (texto o checklist interactivo) queda documentado con su justificación (ver §11.1) |
| B3 | Como usuario, quiero cancelar la selección sin cerrar el programa | S | Opción "0 / cancelar" disponible |
| B4 | Como usuario, NO debo poder seleccionar secciones en las que no estoy matriculado | **Won't** (bloqueo explícito, no una funcionalidad a construir) | La lista ofrecida para selección proviene únicamente de la respuesta de matrícula del usuario autenticado; nunca de un `sectionId` ingresado o descubierto manualmente (ver §11.2) |
| B5 | Como usuario, quiero poder elegir opcionalmente un período académico distinto al actual, para listar y descargar cursos ya cursados | C | Por defecto solo se muestra el período vigente; una opción explícita ("ver períodos anteriores") repite el flujo B1→B2 con otro `academicPeriodId` (ver §11.3) |

### Épica C — Descarga (motor ya construido; se valida que el contrato con B se mantenga intacto)

| ID | Historia | Prioridad | Criterios de aceptación |
|---|---|---|---|
| C1 | Como usuario, quiero que no se descarguen archivos ya existentes | M (cumplido) | `skip_exist` verificado por tamaño > 0 |
| C2 | Como usuario, quiero que no se descarguen íconos de interfaz ni duplicados de audio | M (cumplido) | Filtro de dominio S3 + lista blanca de extensiones |
| C3 | Como usuario, quiero ver progreso en tiempo real por curso seleccionado | M (cumplido) | TUI muestra curso actual, progreso, últimos eventos |

### Épica D — Preparación para GUI

| ID | Historia | Prioridad | Criterios de aceptación |
|---|---|---|---|
| D1 | Como responsable del proyecto, quiero que la lógica de negocio no dependa de una librería de presentación concreta | S | ADR aprobado antes de tocar la implementación |
| D2 | Como responsable del proyecto, quiero un mockup de la futura GUI validado antes de implementarla | S | Mockup revisado contra los flujos de las Épicas A, B y C |

### Épica E — Documentación y gestión

| ID | Historia | Prioridad | Criterios de aceptación |
|---|---|---|---|
| E1 | Como responsable del proyecto, quiero un registro de decisiones de último minuto | M | Decision Log activo desde el Sprint 0 |
| E2 | Como responsable del proyecto, quiero un catálogo de errores conocidos y su tratamiento | M | Matriz de errores ampliada (§8) |
| E3 | Como responsable del proyecto, quiero casos de prueba manuales para cada historia Must | M | Plan de pruebas (§9) |

---

## 7. Sprints

Cada sprint produce **documentación, casos de prueba y mockups**, no código.

### Sprint 0 — Fundación
**Objetivo:** dejar listo el marco de gestión antes de tocar requisitos técnicos.
- Entregable: plantillas de Decision Log, matriz de errores, test case; Product Backlog aprobado.
- Revisión: ¿el backlog cubre las 4 épicas del requerimiento original? ✅

### Sprint 1 — Especificación de Autenticación unificada (Épica A)
- Tareas: máquina de estados del login (§10.1... ver también sección técnica más abajo); matriz de errores de login; casos de prueba manual (bloque A, §9).
- Entregable: especificación funcional del módulo de auth + matriz de errores.
- Revisión: ¿cada estado del login tiene una salida definida (éxito, error, reintento)? ¿La contraseña queda fuera de cualquier log?

### Sprint 2 — Especificación de Descubrimiento y Selección (Épica B)
- Tareas: definir sintaxis exacta del mecanismo de selección; evaluar checklist interactivo vs. prompt de texto en terminales embebidas (ver §11.1); especificar comportamiento ante lista de cursos vacía o sin `sectionId`; mockup textual de la pantalla de selección (§12.1); casos de prueba (bloque B, §9).
- Entregable: especificación de selección + mockup TUI validado + decisión documentada del mecanismo elegido.
- Revisión: ¿un usuario nuevo entendería qué hacer sin leer un manual?

### Sprint 3 — Validación de integración con la Descarga (Épica C)
- Tareas: mapear campo por campo la salida de B1 hacia la entrada que espera el motor de descarga; detectar incompatibilidades de nombres de campo (`sectionCode` vs. `sectionId`, ya inconsistente entre las dos demos de autenticación — ver §10); casos de prueba de regresión (bloque C, §9).
- Entregable: tabla de mapeo de contratos + lista de incompatibilidades detectadas.
- Revisión: ¿queda claro qué campo usar como fuente única de verdad para `sectionId`?

### Sprint 4 — Arquitectura para GUI + Mockup (Épica D)
- Tareas: ADR de separación de presentación y lógica de negocio; mockups de baja fidelidad de login, selección y progreso (§12.2); contrato de eventos documentado en prosa.
- Entregable: ADR + 3 mockups + contrato de eventos.
- Revisión: ¿los mockups cubren los mismos flujos ya validados en TUI (Sprints 1 y 2), sin funcionalidades no pedidas?

### Sprint 5 — Consolidación documental (Épica E)
- Tareas: unificar Decision Log; unificar matriz de errores; consolidar plan de pruebas; actualizar este informe técnico con lo nuevo.
- Entregable: este documento, como base para la futura implementación.
- Revisión final: ¿todos los requisitos originales (1–4) tienen documentación de respaldo? Ver §14.

---

## 8. Matriz de errores y casos borde

| Escenario | Módulo | Comportamiento esperado | Estado |
|---|---|---|---|
| Timeout en formulario de login (red lenta) | Auth | Reintento único con timeout ampliado; si falla, mensaje claro + captura de pantalla | Ya mitigado |
| Popup "¿Mantener sesión iniciada?" no aparece | Auth | `try/except` silencioso, continuar flujo | Ya implementado |
| Credenciales incorrectas | Auth | Detectar mensaje de error del SSO, terminar con mensaje explícito; **no reintentar automáticamente con la misma contraseña** (riesgo de bloqueo de cuenta institucional) | Especificado (Sprint 1) |
| Token no capturado tras login exitoso | Auth → Selección | Abortar con mensaje explícito, no continuar a selección | Especificado (Sprint 1) |
| `academicPeriodId` no encontrado (sin `CURRENT_PERIOD`) | Selección | Abortar con mensaje explícito; no asumir un período por defecto | Especificado (Sprint 2) |
| API de cursos devuelve lista vacía | Selección | Mostrar "no tienes cursos matriculados este período", terminar sin error | Especificado (Sprint 2) |
| Selección inválida del usuario (ej. índice inexistente) | Selección | Re-preguntar sin cerrar el programa, máximo 3 intentos | Especificado (Sprint 2) |
| Curso sin `sectionId` válido en la respuesta de matrícula | Selección → Descarga | Excluir de la lista seleccionable, avisar en el registro | Especificado (Sprint 2/3) |
| `sectionId` de un curso ajeno a la matrícula del usuario | Selección | Bloqueo estructural: nunca se ofrece como opción (ver Épica B4, §11.2) | Especificado (Sprint 2) |
| Período histórico sin cursos registrados | Selección (B5) | Mismo tratamiento que período actual vacío | Especificado (Sprint 2) |
| Token expira a mitad de la descarga (>24h) | Descarga | Error se registra, continúa con el siguiente curso | Ya implementado |
| Archivo ya existe pero con tamaño 0 (descarga previa corrupta) | Descarga | Se re-descarga porque falla la validación `getsize > 0` | Ya implementado |
| Formato fuera de la lista blanca | Descarga | Contabilizado en "filtrados por formato" | Ya implementado |
| Interrupción manual (Ctrl+C) durante la selección | Selección | Cerrar limpiamente cualquier recurso del navegador abierto por la fase de auth | Especificado (Sprint 2) |

---

## 9. Plan de pruebas manuales

### Bloque A — Autenticación
| # | Caso | Entrada | Resultado esperado |
|---|---|---|---|
| A-01 | Login exitoso | Usuario/clave válidos | Tokens capturados, período resuelto |
| A-02 | Contraseña incorrecta | Clave inválida | Mensaje de error claro, sin captura de tokens, sin reintento automático |
| A-03 | Popup de sesión no aparece | — | Continúa sin bloquear |
| A-04 | Red interrumpida durante el login | Desconexión simulada | Timeout controlado, screenshot guardado, mensaje explícito |

### Bloque B — Selección de cursos
| # | Caso | Entrada | Resultado esperado |
|---|---|---|---|
| B-01 | Selección de un solo curso | `"2"` | Solo ese curso pasa a descarga |
| B-02 | Selección múltiple | `"1,3"` | Ambos cursos pasan a descarga |
| B-03 | Selección "todos" | `"todos"` | Todos los cursos listados pasan a descarga |
| B-04 | Selección inválida | `"abc"` | Re-prompt, sin cerrar el programa |
| B-05 | Lista de cursos vacía | (API devuelve `[]`) | Mensaje "sin cursos", terminación limpia |
| B-06 | Selección de período histórico sin cursos | Período anterior elegido, respuesta vacía | Mismo tratamiento que B-05 |

### Bloque C — Regresión de descarga
| # | Caso | Resultado esperado |
|---|---|---|
| C-01 | Curso con archivo ya descargado | `skip_exist`, no se re-descarga |
| C-02 | Contenido con ícono de interfaz embebido | Excluido por filtro de dominio |
| C-03 | Video con MP4 + MP3 + PDF | Solo se descarga MP4 y PDF (MP3 excluido por defecto) |

---

## 10. Decision Log

| Sprint | Decisión | Alternativas consideradas | Justificación | Estado |
|---|---|---|---|---|
| Sprint 1 | No reintentar login automáticamente ante contraseña incorrecta | Reintento automático con nuevo prompt | Evita bloqueos de cuenta por intentos fallidos repetidos | Cerrada |
| Sprint 2 | Mecanismo de selección de cursos: se evaluará checklist interactivo (`questionary`/`InquirerPy`) frente al prompt de texto actual (`rich.prompt`) | Solo prompt de texto | El checklist es más intuitivo, pero debe validarse en terminales embebidas antes de adoptarse (ya hubo un problema similar con `rich screen=True` en IDEs) | Abierta — se cierra en Sprint 2 |
| Sprint 2 | El acceso a secciones se restringe estructuralmente a las que provienen de la matrícula real del usuario autenticado | Permitir ingresar cualquier `sectionId` manualmente | Preserva el alcance ético ya declarado del proyecto (no acceder a contenido de otros estudiantes) | Cerrada |
| Sprint 2 | Los períodos académicos anteriores se ofrecen como opción explícita, no por defecto | Mostrar siempre todos los períodos | Mantiene el flujo principal simple; el historial ya está disponible sin trabajo adicional, se agrega como mejora opcional (B5) | Cerrada |
| Sprint 3 | Unificar el nombre de campo de sección como `sectionId` (fuente única de verdad) | Mantener múltiples alias (`sectionCode`, `section`) como en las demos actuales | Reduce ambigüedad en el contrato entre módulos | Abierta — requiere confirmar contra la respuesta real de la API |
| Sprint 4 | Framework de GUI aún sin decidir (se evalúa entre `PySimpleGUI`/`FreeSimpleGUI` y `PyQt`/`PySide`) | Decidir ya el framework | Se prioriza validar el mockup y el contrato de eventos antes de comprometerse a una librería | Abierta — se cierra en Sprint 4 |

> Versión formal navegable de estas decisiones (nov. 2026): [`docs/adr/README.md`](./docs/adr/README.md) — los ADRs individualizados son la versión activa; esta tabla sigue como registro histórico de origen.

### 10.1 Especificación de la máquina de estados del login (Sprint 1)

```
INICIO → CARGANDO_SSO → ESPERANDO_USUARIO → ESPERANDO_CLAVE
   → CONFIRMANDO_SESION? → CARGANDO_DASHBOARD
   → CAPTURANDO_TOKENS → RESOLVIENDO_PERIODO → LISTO_PARA_SELECCION

Salidas de error posibles desde cualquier estado:
   → ERROR_TIMEOUT | ERROR_CREDENCIALES | ERROR_TOKEN_NO_CAPTURADO | ERROR_PERIODO_NO_ENCONTRADO
```

### 10.2 Incompatibilidad detectada entre demos (a resolver en Sprint 3)

Una de las demos de autenticación busca el identificador de sección en el orden `sectionId → sectionCode → section`; la otra lo busca en el orden `section → sectionCode → sectionId`. Es una inconsistencia real que debe resolverse con una única fuente de verdad antes de integrar, no arrastrarse al nuevo diseño.

---

## 11. Preguntas de diseño resueltas

### 11.1 ¿Es obligatorio escribir el número para seleccionar cursos?

No. Es una decisión de diseño abierta, no una limitación técnica.

| Enfoque | Librería típica | Ventaja | Desventaja |
|---|---|---|---|
| Prompt de texto (`"1,3"` / `"todos"`) | `rich.prompt` | Cero dependencias nuevas | Menos intuitivo, propenso a errores de tipeo |
| Checklist interactivo (flechas + espacio) | `questionary` / `InquirerPy` | Más intuitivo, estándar en CLIs modernas | Comportamiento potencialmente distinto en terminales embebidas |
| Menú de selección simple (radio) | `simple-term-menu` | Muy ligero | No soporta selección múltiple nativamente |

**Decisión:** se evalúa el checklist interactivo explícitamente en terminales embebidas antes de adoptarlo, dado que ya hubo un problema de compatibilidad similar documentado con `rich screen=True` en este mismo proyecto.

### 11.2 ¿Se puede descargar contenido de otra sección del mismo curso?

**Plano técnico:** el endpoint usa `courseId` y `sectionId` como parámetros independientes en la URL; nada en el diseño actual impide, en teoría, construir esa URL con el `sectionId` de otra sección.

**Plano de alcance y ética:** el proyecto declara explícitamente que solo opera sobre contenido al que el usuario tiene acceso legítimo como estudiante matriculado, y que no accede a contenido de otros estudiantes o docentes. Acceder a la sección de otro estudiante rompe esa premisa, aunque el backend lo permitiera técnicamente.

**Decisión:** se trata como **fuera de alcance explícito** (historia B4, prioridad Won't). La lista de cursos/secciones ofrecida para selección proviene únicamente de la respuesta de matrícula real del usuario autenticado, nunca de un identificador ingresado o descubierto manualmente.

### 11.3 ¿Se pueden listar y descargar cursos de períodos anteriores?

Sí. La respuesta del endpoint de períodos académicos ya contiene el listado completo de períodos, no solo el actual — de ahí que el diseño actual tenga que filtrar explícitamente `CURRENT_PERIOD` para quedarse con uno. Los demás períodos ya llegan en la misma respuesta y simplemente se descartan.

**Decisión:** se agrega como historia opcional (B5, prioridad Could). Por defecto el flujo sigue mostrando solo el período vigente (cero fricción para el caso de uso principal); una opción explícita permite listar y seleccionar períodos anteriores, repitiendo el mismo flujo de selección con otro `academicPeriodId`.

---

## 12. Mockups

### 12.1 TUI — Pantalla de selección de cursos

```
┌─ 📚 Cursos disponibles — 2026 Ciclo 2 Agosto PREG ─────────────┐
│  [1] Mecánica Clásica            (sección A)                   │
│  [2] Cálculo III                 (sección B)                   │
│  [3] Programación Avanzada       (sección A)                   │
└──────────────────────────────────────────────────────────────┘
Selecciona curso(s) [ej: 1  |  1,3  |  todos  |  0=cancelar]: _
```

### 12.2 GUI futura — 3 pantallas mínimas

```
[Pantalla 1: Login]              [Pantalla 2: Selección]         [Pantalla 3: Progreso]
 ┌────────────────┐               ┌────────────────────┐         ┌──────────────────────┐
 │ Usuario  [___]  │               │ ☐ Mecánica Clásica  │         │ Curso: Mecánica Clás. │
 │ Clave    [___]  │   ───────►    │ ☐ Cálculo III       │  ────►  │ ████████░░░  62%      │
 │ [Iniciar sesión]│               │ ☐ Prog. Avanzada    │         │ Archivo: guia_03.pdf  │
 └────────────────┘               │   [Descargar seleccion.]│     │ ✅ 24  ⏭ 3  ❌ 0       │
                                    └────────────────────┘         └──────────────────────┘
```

*Wireframes de referencia únicamente, validados contra los flujos de las Épicas A y B antes de elegir el framework definitivo en Sprint 4.*

---

## 13. Tablero Kanban

| Backlog | Por hacer | En progreso | En revisión | Hecho |
|---|---|---|---|---|
| Selección de framework GUI | Especificar mecanismo de selección (checklist vs. texto) | — | — | Login SSO automático |
| Historial de períodos anteriores (B5) | Especificar máquina de estados del login | — | — | Descarga con deduplicación y filtro de dominio |
| Reintentos con backoff | Especificar contrato de datos entre selección y descarga | — | — | TUI con `rich.Live` |
| Detección de expiración de token en vivo | Mockup de selección de cursos (TUI) | — | — | Matriz de incidencias original |
| Paralelización de descargas | ADR de arquitectura modular | — | — | Análisis de necesidad de datos (§3) |
| Exportar reporte CSV/JSON | Mockups de GUI (3 pantallas) | — | — | Backlog completo (Épicas A–E) |
| Manual de usuario GUI | Consolidar Decision Log y matriz de errores | — | — | Resolución de las 3 preguntas de diseño (§11) |

---

## 14. Checklist de cobertura de requisitos

| Requisito original | Sección que lo cubre | ¿Documentado? |
|---|---|---|
| 1. Login automático completo | Épica A, §7 Sprint 1, §10.1 | ✅ |
| 2. Descarga automática con obtención y selección de cursos | Épicas B y C, §7 Sprints 2–3 | ✅ |
| 3. Preparación para migración a GUI (en Python) | Épica D, §4, §7 Sprint 4 | ✅ |
| 4. Documentación completa del proyecto, fases, tablero | Épica E, §7 Sprint 5, §13 | ✅ |
| Casos de error y de cambio | §8, §10 (transversal a todos los sprints) | ✅ |
| Necesidad real de cada dato capturado | §3 | ✅ |
| Mecanismo de selección (texto vs. checklist) | §11.1 | ✅ |
| Alcance sobre secciones ajenas | §11.2 | ✅ |
| Cursos de períodos anteriores | §11.3 | ✅ |

---

## 15. Consideraciones éticas y de seguridad

- El sistema solo accede a contenido al que el usuario ya tiene acceso legítimo como estudiante matriculado, mediante su propia sesión autenticada.
- El acceso está estructuralmente restringido a las secciones que provienen de la matrícula real del usuario (ver §11.2); no se ofrece ni se documenta ningún mecanismo para acceder a secciones ajenas.
- La contraseña del usuario se usa únicamente en el instante del login y nunca se almacena en disco ni en logs.
- **El token de sesión (`AUTH_TOKEN`) equivale a la contraseña mientras esté vigente.** No debe compartirse, publicarse en repositorios, ni pegarse en chats o servicios externos.
- **Advertencia crítica antes de publicar este proyecto en un repositorio público:** algunas versiones tempranas del script y del informe técnico contienen un token JWT real embebido directamente en el código fuente como ejemplo. **Antes de subir el repositorio a GitHub es indispensable:**
  1. Eliminar o reemplazar cualquier valor real de `AUTH_TOKEN`, `USER_ID` y `TENANT_ID` por marcadores de ejemplo (`"TU_TOKEN_AQUI"`, etc.).
  2. Revisar el historial de git (no solo el estado actual de los archivos) para asegurarse de que ningún commit previo conserve el token real.
  3. Si el token ya fue expuesto en algún momento, cerrar sesión en `class.utp.edu.pe` para invalidarlo antes de publicar.
  4. Añadir un archivo `.gitignore` que excluya cualquier archivo de configuración con credenciales reales (ver README).
- Se recomienda uso estrictamente personal (estudio offline, respaldo); no se recomienda la redistribución pública del material académico descargado, dado que pertenece a la institución y a los autores originales del contenido.
- Se recomienda revisar el reglamento y los términos de uso de la plataforma antes de un uso extensivo o automatizado.

---

## 16. Próximos pasos

1. Cerrar las decisiones abiertas del Decision Log (§10): mecanismo de selección, nombre único de campo de sección, framework de GUI.
2. Completar el Sprint 3 (mapeo de contratos entre selección y descarga) antes de iniciar cualquier implementación.
3. Validar los mockups del Sprint 4 contra los flujos ya definidos en los Sprints 1 y 2.
4. Recién al cerrar el Sprint 5 (documentación consolidada), pasar a una fase de implementación real, fuera del alcance de este informe.
