# Reporte TÃ©cnico de IngenierÃ­a Inversa: Demo de AutenticaciÃ³n UTP+class (HISTÃ“RICO, SANEADO)

> **Documento histÃ³rico** â€” fase de demo de autenticaciÃ³n, previa al rediseÃ±o v3. Registrado en el Decision Log del INFORME_TECNICO.md como evidencia de origen; el informe vigente es la fuente canÃ³nica. **Saneado:** `user-id`, `tenant-id`, periodId y token reales fueron reemplazados por marcadores de ejemplo. **Saneado:** los identificadores reales (`user-id`, `tenant-id`, token y cÃ³digo de estudiante) fueron reemplazados por marcadores de ejemplo; jamÃ s publicar los valores reales (ver README, secciÃ³n Seguridad).

---

## 1. Contexto y Objetivos del Sistema

El proyecto tiene como finalidad el desarrollo de una soluciÃ³n automatizada en Python para realizar la autenticaciÃ³n, captura de tokens de sesiÃ³n y extracciÃ³n de datos acadÃ©micos (cursos, secciones y tareas) desde la plataforma **UTP+class** (`[https://class.utp.edu.pe](https://class.utp.edu.pe)`).

### Objetivos Clave

* **AutenticaciÃ³n sin intervenciÃ³n manual:** Automatizar el login mediante **Playwright** superando las redirecciones del SSO de Microsoft y portales institucionales.
* **Captura transparente de credenciales:** Registrar los encabezados HTTP emitidos en segundo plano (`AUTH_TOKEN`, `USER_ID`, `TENANT_ID`).


* **ExtracciÃ³n dinÃ¡mica no hardcodeada:** Consultar la API del backend (`api-pao.utpxpedition.com`) para obtener la lista real de asignaturas sin recurrir a datos estÃ¡ticos en el cÃ³digo.


* **VisualizaciÃ³n profesional:** Renderizar el estado de ejecuciÃ³n, las credenciales capturadas y el payload JSON utilizando la librerÃ­a **Rich**.



---

## 2. Perfil de Usuario y ParÃ¡metros de Entorno

Usuario de pruebas: cÃ³digo institucional del propio usuario (saneado).


* **Entorno de ejecuciÃ³n:** Python 3.11 / Node runtime de Playwright[cite: 5, 7].
* **URL Base de la Plataforma:** `[https://class.utp.edu.pe](https://class.utp.edu.pe)`.


* **Endpoint Principal de Cursos:** `[https://api-pao.utpxpedition.com/course/student/courses](https://api-pao.utpxpedition.com/course/student/courses)`.


* **Ciclo AcadÃ©mico Obtenido:** `2026 - Ciclo 2 Agosto PREG (001)` (ID de perÃ­odo: `95fdb1ee-1b96-5f61-ab7e-000000000000`).



---

## 3. Desglose TÃ©cnico de Incidencias, Causa RaÃ­z y Soluciones

### Incidencia 1: Fallo de Timeout en Selector de Bienvenida (`Timeout 15000ms exceeded`)

* **SÃ­ntoma:** La consola mostrÃ³ el error `Page.wait_for_selector: Timeout 15000ms exceeded` esperando el locator `"text=Mis cursos"`.


* **AnÃ¡lisis de Causa RaÃ­z:**
1. El usuario ingresÃ³ Ãºnicamente `TU_CODIGO` en el prompt.


2. El flujo de autenticaciÃ³n SSO de Microsoft redirige por mÃºltiples URLs y muestra ventanas emergentes intermedias (como la solicitud de *"Â¿Desea mantener la sesiÃ³n iniciada?"*).


3. El selector `"text=Mis cursos"` fue buscado antes de que el frontend de la Single Page Application (SPA) terminara el renderizado DOM post-redirecciÃ³n.




* **SoluciÃ³n Aplicada:**
* ImplementaciÃ³n de selectores genÃ©ricos para el formulario de login: `input[type='text']`, `input[type='email']`, `input[type='password']`.


* AdiciÃ³n del manejador explÃ­cito para el botÃ³n de confirmaciÃ³n de sesiÃ³n de Microsoft (`#idSIButton9`).





---

### Incidencia 2: Bloqueo Indefinido por Estado de Carga `networkidle`

* **SÃ­ntoma:** Error `Timeout 30000ms exceeded` en el evento de carga del navegador.


* **AnÃ¡lisis de Causa RaÃ­z:**
1. La instrucciÃ³n `page.wait_for_load_state("networkidle")` requiere que no existan mÃ¡s de 2 peticiones de red activas durante al menos 500 ms.


2. La inspecciÃ³n del dashboard en la captura `error_login.png` demostrÃ³ que **el inicio de sesiÃ³n fue exitoso** y la interfaz cargÃ³ correctamente.


3. No obstante, la pÃ¡gina contiene banners dinÃ¡micos (ej. *"ENCUESTA ALUMNO UTP"*), carruseles e inicializadores de analÃ­tica que ejecutan consultas asÃ­ncronas en bucle (`polling`). Esto impidiÃ³ que la red entrara en reposo absoluto.




* **SoluciÃ³n Aplicada:**
* SustituciÃ³n del evento `networkidle` por la estrategia `wait_until="domcontentloaded"` en `page.goto()`.


* SincronizaciÃ³n mediante la espera directa de un nodo HTML estable en el dashboard: `page.wait_for_selector("text=Actividades semanales")`.





---

### Incidencia 3: Presencia de Datos EstÃ¡ticos Simulados (*Hardcoding*)

* **SÃ­ntoma:** El script renderizaba tablas con cursos y profesores utilizando diccionarios fijos en Python.


* **AnÃ¡lisis de Causa RaÃ­z:** Incompatibilidad entre la simulaciÃ³n visual y la extracciÃ³n en tiempo real del backend.


* **SoluciÃ³n Aplicada:**
* EliminaciÃ³n de todas las estructuras fijas de asignaturas.


* ImplementaciÃ³n del evento de intercepciÃ³n de red de Playwright (`page.on("response", handle_response)`) para escuchar y almacenar pasivamente todas las respuestas emitidas por `api-pao.utpxpedition.com`.





---

### Incidencia 4: Respuesta HTTP 500 al Consultar la API Externa

* **SÃ­ntoma:** `Error al consultar la API de cursos: 500 Server Error for url: [https://api-pao.utpxpedition.com/course/student/courses](https://api-pao.utpxpedition.com/course/student/courses)`.


* **AnÃ¡lisis de Causa RaÃ­z:**
1. Al realizar una peticiÃ³n aislada mediante la librerÃ­a externa `requests` de Python, el servidor rechazÃ³ la solicitud.


2. La API requiere explÃ­citamente el parÃ¡metro de consulta `academicPeriodId` (ej. `?academicPeriodId=95fdb1ee-1b96-5f61-ab7e-000000000000`), ademÃ¡s de cabeceras de contexto especÃ­ficas (`x-tenant-id`, `user-id`, `user-role`).




* **SoluciÃ³n Aplicada:**
* Descarte de consultas externas desacopladas con `requests`.
* AdopciÃ³n de inyecciÃ³n de cÃ³digo dentro del navegador (`page.evaluate()`), ejecutando un `fetch` nativo dentro del mismo contexto autenticado del usuario.



---

### Incidencia 5: Captura de Payloads Secundarios e Irrelevantes

* **SÃ­ntoma:** La consola devolviÃ³ respuestas JSON de estructuras no deseadas:
1. El listado de perÃ­odos acadÃ©micos (`academicPeriods`).
2. Objeto de conteo de mensajes/notificaciones: `{"success": true, "code": 2, "data": {"count": 0, "userIdsTo": []}}`.


* **AnÃ¡lisis de Causa RaÃ­z:** Durante la carga inicial, la SPA de UTP realiza mÃºltiples peticiones simultÃ¡neas a varios endpoints del microservicio `api-pao`. La intercepciÃ³n genÃ©rica capturaba el primer paquete JSON que respondiera el servidor.
* **SoluciÃ³n Aplicada:**
1. **Fase 1:** Parsear la respuesta de perÃ­odos acadÃ©micos para extraer el ID correspondiente al objeto con `type: "CURRENT_PERIOD"` y `period != "9999"` (`2026 - Ciclo 2 Agosto PREG (001)`).


2. **Fase 2:** Invocar explÃ­citamente el endpoint de cursos inyectando el parÃ¡metro `academicPeriodId` mediante `page.evaluate()` y filtrar el resultado asegurando la presencia de las claves `name`, `courseName` o `sectionId`.



---

## 4. Matriz Comparativa del Flujo de Desarrollo

| Componente / Criterio     | VersiÃ³n 1 (Inicial)                                       | VersiÃ³n 2 (Intermedia)                                    | VersiÃ³n 3 (Final Corregida)                                                 |
|---------------------------|-----------------------------------------------------------|-----------------------------------------------------------|-----------------------------------------------------------------------------|
| **Flujo de Login**        | Intento de login por correo completo con timeouts cortos. | Manejo de cÃ³digo de usuario + bypass de SSO de Microsoft. | Flujo secuencial robusto con manejo de popups e inspecciÃ³n de selectores.   |
| **SincronizaciÃ³n de Red** | Espera del selector `"text=Mis cursos"`.                  | Espera global `networkidle` (Causa de cuelgue).           | Espera de DOM (`domcontentloaded`) + Selector `text=Actividades semanales`. |
| **Origen de los Datos**   | Estructuras hardcodeadas en Python.                       | Consulta externa con `requests` (Error 500).              | IntercepciÃ³n pasiva + `fetch` nativo inyectado en el navegador autenticado. |
| **Formato de Salida**     | ImpresiÃ³n bÃ¡sica en consola.                              | Tablas Rich con datos simulados.                          | Tablas Rich dinÃ¡micas + Renderizado de JSON nativo (`console.print_json`).  |

---

## 5. Arquitectura y Diagrama de Flujo de la SoluciÃ³n Final

```
 [1. Inicio Playwright] â”€â”€â–º [2. Formulario Microsoft SSO] â”€â”€â–º [3. Bypass #idSIButton9]
                                                                        â”‚
                                                                        â–¼
 [6. Consola Rich / JSON] â—„â”€â”€ [5. InyecciÃ³n page.evaluate] â—„â”€â”€ [4. Captura Headers & PeriodID]

```

### Protocolo de ExtracciÃ³n Paso a Paso

1. **InicializaciÃ³n de Browser Context:** Se arranca Chromium en Playwright registrando el listener de eventos `page.on("response", handle_response)`.


2. **AutenticaciÃ³n en SSO:**
* InyecciÃ³n del cÃ³digo de estudiante (`TU_CODIGO`).


* InyecciÃ³n de la contraseÃ±a del usuario.
* Clic condicional en el botÃ³n de persistencia de sesiÃ³n (`idSIButton9`).




3. **Monitoreo de Encabezados:** Durante la transiciÃ³n, el listener captura de los headers de solicitud:
* `authorization`: Token JWT en formato Bearer (`eyJhbGciOi...`).


* `user-id`: Identificador Ãºnico del usuario en el backend (`04aba43a-d977-5c02-0000-000000000000`).


* `x-tenant-id`: Identificador de la organizaciÃ³n (`a5f469d2-3c0e-5c68-0000-000000000000`).




4. **ObtenciÃ³n del PerÃ­odo AcadÃ©mico:** Se examina la respuesta del endpoint de perÃ­odos para extraer la clave `id` del ciclo marcado como `CURRENT_PERIOD` (`95fdb1ee-1b96-5f61-ab7e-000000000000`).
5. **EjecuciÃ³n de Fetch Interno:** Se ejecuta dentro del navegador la siguiente instrucciÃ³n JavaScript:
```javascript
fetch("https://api-pao.utpxpedition.com/course/student/courses?academicPeriodId=95fdb1ee-1b96-5f61-ab7e-000000000000")

```


6. **Formateado y Renderizado:** La respuesta es procesada por **Rich** para mostrar el cuadro de credenciales, la tabla de materias y la estructura del JSON nativo en pantalla.



---

## 6. Estado Operativo del Sistema

* **Estatus de AutenticaciÃ³n:** Exitoso. Supera las validaciones de Microsoft SSO sin requerir intervenciÃ³n humana.


* **Captura de Tokens de Red:** Captura en tiempo real del token de autorizaciÃ³n Bearer, `USER_ID` y `TENANT_ID`.


* **Fidelidad de Datos:** EliminaciÃ³n completa de datos de prueba o valores estÃ¡ticos. El sistema procesa y proyecta Ãºnicamente la respuesta real del servidor de la universidad.