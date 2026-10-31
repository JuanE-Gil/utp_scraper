# UTP+class Downloader — Plan de diseño UX/UI de la GUI

**Fecha:** 30 de octubre de 2026
**Base analizada:** `ui_gui.py` (GUI v1, `feature/gui`) y `estado_proyecto_fase2_gui.md`
**Alcance:** solo diseño. Este documento **no modifica `ui_gui.py`** ni incluye código; define qué construir y con qué valores.
**Convención:** lo marcado *(no verificado)* es una hipótesis que hay que comprobar en tu equipo antes de darla por cierta.

---

## Índice

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Diagnóstico de la GUI v1](#2-diagnóstico-de-la-gui-v1)
3. [Límites del framework y niveles de ejecución](#3-límites-del-framework-y-niveles-de-ejecución)
4. [Principios de diseño](#4-principios-de-diseño)
5. [Sistema visual](#5-sistema-visual)
6. [Estructura de ventana y navegación](#6-estructura-de-ventana-y-navegación)
7. [Especificación de pantallas](#7-especificación-de-pantallas)
8. [Biblioteca de componentes](#8-biblioteca-de-componentes)
9. [Microcopy](#9-microcopy)
10. [Accesibilidad](#10-accesibilidad)
11. [Dependencias con el código y el plan](#11-dependencias-con-el-código-y-el-plan)
12. [Plan de implementación del rediseño](#12-plan-de-implementación-del-rediseño)
13. [Criterios de aceptación y QA visual](#13-criterios-de-aceptación-y-qa-visual)
14. [Riesgos y decisiones abiertas](#14-riesgos-y-decisiones-abiertas)

---

## 1. Resumen ejecutivo

La GUI v1 funciona y respeta el contrato de eventos, pero se ve como un prototipo: tres ventanas de tamaños distintos que se abren y cierran, fuente por defecto, sin paleta, lista plana de casillas con textos repetidos y un resumen final en un popup estándar.

La propuesta es un **sistema visual claro con acentos azul y violeta vivos en tono pastel**, sobre fondos lavanda muy suaves y tarjetas blancas, con tipografía Segoe UI, cuadrícula de espaciado de 4 px y una **ventana única** con cuatro vistas (Acceso → Cursos → Descarga → Resumen) y un indicador de pasos.

Tres decisiones condicionan todo lo demás:

1. **Los tonos pastel vivos no sirven como fondo de texto blanco.** `#6C8CFF` y `#9B7BFF` dan ≈ 3,1:1 con blanco. Por eso el plan usa los pastel vivos para superficies, chips, fondos y degradados, y reserva dos tonos más profundos de la misma familia (`#4A5FE8` y `#7C4DFF`) para botones y textos de acción (≈ 5,1:1 y ≈ 4,8:1).
2. **Tkinter no tiene esquinas redondeadas, sombras ni degradados nativos.** El diseño se plantea en tres niveles (sección 3). La recomendación es un nivel base plano y pulido, con imágenes PNG solo para marca, cabecera e iconos.
3. **La licencia de FreeSimpleGUI es LGPLv3+, no MIT.** Lo verifiqué en los metadatos del paquete 5.1.0 instalado. El ADR-0006 la describe como MIT, así que debe corregirse antes de cerrarlo (sección 14).

---

## 2. Diagnóstico de la GUI v1

Hallazgos observados **en el código** de `ui_gui.py`, con su corrección de diseño.

| # | Observación en `ui_gui.py` | Impacto en el usuario | Corrección de diseño |
|---|---|---|---|
| 1 | Tres ventanas independientes (430×210, 620×640, 940×560) que se cierran y se abren en secuencia. | La ventana "salta" de tamaño y posición; se pierde la sensación de aplicación. | Ventana única con vistas intercambiables (sección 6). Alternativa mínima: mismo tamaño y posición para las tres. |
| 2 | Fuente `"SegoeUi"` en los títulos. | *(No verificado)* El nombre de familia de Windows es `Segoe UI`, con espacio; sin él Tk probablemente cae a la fuente por defecto y el título no se ve como se pretende. | Usar `Segoe UI` y `Segoe UI Semibold`; confirmar en pantalla. |
| 3 | Login sin tecla Enter asociada al botón y sin mostrar/ocultar contraseña. | Hay que usar el ratón; si la clave se teclea mal no hay forma de comprobarla. | Enter envía; botón de ojo; foco inicial en el usuario (ya existe). |
| 4 | `login()` se llama dentro del bucle de eventos. | La ventana se congela durante la petición y no puede mostrar "Autenticando…" de forma real. | Estado de carga visible, lo que exige llamarlo en un hilo (sección 11). |
| 5 | Error de login en el mismo estilo que el texto normal. | El error pasa desapercibido. | Banner con color, icono y texto, con el espacio reservado para que el diseño no salte. |
| 6 | Cada casilla lleva el texto completo: `"<ciclo> · vigente <curso> [<n.º>]"` repetido en todas las filas. | Ruido visual: el nombre del ciclo ya aparece en el encabezado del grupo. | Cabecera de grupo con el ciclo; filas solo con curso y metadatos. |
| 7 | Todos los ciclos visibles a la vez, sin plegar; sin "seleccionar todo" por grupo ni contador. | Con 31 cursos la lista es larga; no hay noción de cuántos se eligieron. | Acordeón por ciclo (vigente abierto, anteriores plegados), acciones por grupo y contador fijo. |
| 8 | `groups, _ = group_courses_by_period(...)` descarta los excluidos. | El usuario no sabe que algún curso no se puede descargar (la matriz §8 pide avisar). | Aviso discreto con el número de cursos excluidos. |
| 9 | Los nombres de la plataforma llegan en mayúsculas. | Texto pesado y poco legible. | Presentación en minúsculas tipográficas solo para mostrar (opcional, ver sección 8.5). |
| 10 | Botón Cancelar deshabilitado con tooltip "Se habilita con Task 2.4". | Filtra nomenclatura interna al usuario y muestra un control inútil. | Ocultarlo hasta que exista la cancelación real; no exponer nombres de tareas. |
| 11 | La barra solo mide el curso actual; el worker emite `curso_jobs`, que la ventana de progreso no consume. | No se ve el avance global ("curso 2 de 5"). | Barra global calculada en la GUI (sección 7.3). |
| 12 | Cerrar la ventana de progreso rompe el bucle, `run()` sigue y el proceso termina con el hilo daemon aún descargando. | Pérdida silenciosa y, hoy, un archivo parcial (hallazgo 9 del plan). | Confirmación de salida durante la descarga. |
| 13 | Resumen final con `sg.Popup`. | Es la pantalla más importante emocionalmente y la más pobre. | Vista de resumen con tarjetas de cifras y acciones. |
| 14 | Títulos inconsistentes ("Login · …", "2 · Selección…", "3 · Progreso"). | Falta de coherencia. | Un patrón único: "UTP+class Downloader — <vista>". |

---

## 3. Límites del framework y niveles de ejecución

FreeSimpleGUI se apoya en Tkinter. Comprobé en el código fuente de la versión 5.1.0 que existen los parámetros de estilo que usa este plan: `mouseover_colors`, `button_color`, `disabled_button_color`, `bind_return_key`, `checkbox_color`, `bar_color`, colores de barra de desplazamiento (`sbar_*`), `Multiline.print` con color por línea, `margins` y `element_padding` en la ventana, `icon`, `Push`, `pin`, `set_min_size` y `theme_add_new`. *(Esa comprobación fue estática, leyendo la firma de cada clase; no pude ejecutar la interfaz porque el entorno no tiene `tkinter`.)*

**Lo que Tkinter no ofrece de forma nativa:** esquinas redondeadas, sombras, degradados, transiciones animadas, desenfoque y control fino del anillo de foco.

| Nivel | Enfoque | Qué se obtiene | Coste y riesgo |
|---|---|---|---|
| **A. Tk plano pulido** | Solo widgets estándar con paleta, tipografía y espaciado propios. Bordes de 1 px simulados con columnas anidadas. | Aspecto limpio, coherente y estable. Sin dependencias gráficas. | Bajo. Sin redondeos ni sombras. |
| **B. A + imágenes** | Nivel A más PNG embebidos para marca, cabecera con degradado, iconos y quizá botones principales redondeados. | Aspecto claramente más "producto". | Medio. Hay que mantener recursos 1x y 2x; los PNG se ven borrosos con escalado de pantalla si no se prepara una versión para 125 % y 150 %. |
| **C. Migrar a PySide6 (Qt)** | Hojas de estilo QSS, esquinas redondeadas, sombras, animaciones, mejor accesibilidad. | Techo visual mucho mayor. | Alto: reescribir `ui_gui.py`, mayor peso del paquete. Se puede hacer sin tocar `core` gracias al contrato de eventos. |

**Recomendación:** ejecutar el **nivel A** como base y añadir del **nivel B** solo lo que más rinde: marca, cabecera con degradado, iconos y spinner. Revisar el nivel C si, tras ver el resultado, el techo visual sigue sin bastar; esa decisión pertenece al ADR-0006, que sigue abierto.

**Decisión de botones:** usar botones clásicos de Tk con colores explícitos (`use_ttk_buttons` desactivado). Los botones ttk toman el aspecto del sistema en Windows y no respetan bien el color de fondo, lo que impediría la paleta.

**Bordes y tarjetas sin esquinas redondeadas:** una columna exterior del color del borde, con un relleno de 1 px, que contiene una columna interior blanca. Evita tocar widgets Tk de bajo nivel.

---

## 4. Principios de diseño

1. **Claridad antes que decoración.** Una acción principal por pantalla, visualmente dominante.
2. **El estado siempre visible.** Dónde estoy (pasos), qué está pasando (progreso) y qué puedo hacer (botones activos).
3. **Nunca solo color.** Cada estado combina color, icono y texto (accesibilidad y daltonismo).
4. **Lo irreversible se confirma; lo reversible no.** Salir durante una descarga pide confirmación; seleccionar y deseleccionar no.
5. **Honestidad sobre lo que hace la herramienta.** Se muestra que la clave no se guarda y que solo se accede a los cursos propios (ADR-0001, ADR-0002).
6. **Coherencia con la TUI.** Mismos términos y mismos cuatro contadores: Descargados, Ya existían, Filtrados por formato, Errores.

---

## 5. Sistema visual

### 5.1 Paleta (tema claro)

La familia es azul índigo y violeta. Los pastel vivos se usan en superficies y acentos; los tonos profundos, en todo lo que lleva texto blanco.

**Fondos y superficies**

| Token | Hex | Uso |
|---|---|---|
| `bg-app` | `#F5F4FF` | Fondo de la ventana (lavanda muy claro) |
| `surface` | `#FFFFFF` | Tarjetas, campos de entrada |
| `surface-alt` | `#EEF0FF` | Cabeceras de grupo, filas con foco, log |
| `border-soft` | `#DAD8F5` | Bordes decorativos de tarjetas y separadores |
| `border-input` | `#8D8ABF` | Borde de campos y casillas (≈ 3,2:1 sobre blanco) |

**Texto**

| Token | Hex | Uso |
|---|---|---|
| `text-primary` | `#1E1B3A` | Títulos y cuerpo |
| `text-secondary` | `#5B5780` | Metadatos, ayudas |
| `text-disabled` | `#9C99BE` | Controles inactivos |
| `text-on-accent` | `#FFFFFF` | Sobre `accent-blue-600` y `accent-violet-600` |

**Acentos**

| Token | Hex | Uso |
|---|---|---|
| `accent-blue-400` | `#6C8CFF` | Pastel vivo: degradados, decoración, relleno del spinner |
| `accent-blue-600` | `#4A5FE8` | Botón principal, enlaces, barra de progreso, anillo de foco |
| `accent-blue-100` | `#DCE4FF` | Fondo de chips y resaltados azules |
| `accent-blue-700` | `#2F3FB8` | Texto sobre `accent-blue-100` |
| `accent-violet-400` | `#9B7BFF` | Pastel vivo: final del degradado, decoración |
| `accent-violet-600` | `#7C4DFF` | Acento secundario, paso completado, chip "vigente" |
| `accent-violet-100` | `#E7DEFF` | Fondo de chips violetas |
| `accent-violet-700` | `#5B34C9` | Texto sobre `accent-violet-100` |

**Estados** (fondo suave + texto profundo)

| Estado | Fondo | Texto/icono | Uso |
|---|---|---|---|
| Éxito | `#DDF6EA` | `#14693F` | Descargado |
| Aviso | `#FFF1D6` | `#8A5300` | Ya existía, aviso de excluidos |
| Error | `#FFE1E6` | `#B4233F` | Error de login, de curso o de archivo |
| Información / filtrado | `#DCE4FF` | `#2F3FB8` | Filtrado por formato, mensajes neutros |

**Estados interactivos del botón principal:** reposo `#4A5FE8`; sobre el botón `#3F52D6`; deshabilitado fondo `#DAD8F5` con texto `#9C99BE`.

**Degradado de marca** (solo como imagen en la cabecera y el logotipo): horizontal de `#4A5FE8` a `#7C4DFF`, con una variante pastel `#6C8CFF → #9B7BFF` para zonas grandes con texto oscuro encima.

### 5.2 Contrastes calculados

Calculados a mano con la fórmula de contraste de WCAG 2.x; valores aproximados. Conviene confirmarlos con una herramienta antes de congelar la paleta.

| Combinación | Contraste ≈ | Umbral | ¿Cumple? |
|---|---|---|---|
| `#1E1B3A` sobre `#F5F4FF` | 15:1 | 4,5:1 | Sí |
| `#5B5780` sobre blanco | 6,7:1 | 4,5:1 | Sí |
| Blanco sobre `#4A5FE8` | 5,1:1 | 4,5:1 | Sí |
| Blanco sobre `#7C4DFF` | 4,8:1 | 4,5:1 | Sí |
| `#2F3FB8` sobre `#DCE4FF` | 6,6:1 | 4,5:1 | Sí |
| `#5B34C9` sobre `#E7DEFF` | 5,9:1 | 4,5:1 | Sí |
| `#14693F` sobre `#DDF6EA` | 5,9:1 | 4,5:1 | Sí |
| `#8A5300` sobre `#FFF1D6` | 5,7:1 | 4,5:1 | Sí |
| `#B4233F` sobre `#FFE1E6` | 5,3:1 | 4,5:1 | Sí |
| Barra `#4A5FE8` sobre pista `#E3E6FA` | 4,1:1 | 3:1 (gráfico) | Sí |
| Borde de campo `#8D8ABF` sobre blanco | 3,2:1 | 3:1 (componente) | Sí |
| Blanco sobre `#6C8CFF` / `#9B7BFF` | 3,1:1 / 3,2:1 | 4,5:1 | **No** → solo decoración, nunca texto |

### 5.3 Tema oscuro (opcional, fuera de la v1)

La paleta se define como tokens para poder invertirla. Valores de partida, **con contrastes por validar**: fondo `#14122B`, superficie `#1E1B3F`, borde `#34306B`, texto `#ECEBFF`, texto secundario `#A9A6D6`, azul `#7F9BFF`, violeta `#A78BFF`. No se recomienda implementarlo hasta cerrar el tema claro.

### 5.4 Tipografía

| Rol | Familia | Tamaño | Peso | Color |
|---|---|---|---|---|
| Título de vista | Segoe UI Semibold | 18 pt | Semibold | `text-primary` |
| Título de sección / grupo | Segoe UI Semibold | 12 pt | Semibold | `text-primary` |
| Cuerpo y controles | Segoe UI | 10 pt | Regular | `text-primary` |
| Metadatos y ayudas | Segoe UI | 9 pt | Regular | `text-secondary` |
| Cifras de resumen | Segoe UI Semibold | 22 pt | Semibold | según estado |
| Log y rutas | Consolas | 9 pt | Regular | `text-primary` |

Reglas: una sola familia sin serifas; máximo cuatro tamaños por pantalla; sin mayúsculas sostenidas salvo siglas; interlineado cómodo en bloques de más de una línea. *(No verificado)* Confirmar que `Segoe UI Semibold` se resuelve en tu Windows; si no, usar `Segoe UI` en negrita.

### 5.5 Espaciado

Cuadrícula base de **4 px**; todos los valores son múltiplos.

| Token | Valor | Uso típico |
|---|---|---|
| `space-1` | 4 px | Etiqueta → campo; icono → texto |
| `space-2` | 8 px | Entre filas de una lista; entre chips |
| `space-3` | 12 px | Relleno interno de chips y botones pequeños |
| `space-4` | 16 px | Relleno interno de tarjetas; separación entre tarjetas |
| `space-5` | 24 px | Margen lateral de la ventana; entre secciones |
| `space-6` | 32 px | Separación entre bloques grandes; margen superior de la tarjeta de login |

Correspondencia con el framework: márgenes de la ventana 24 px laterales y 20 px verticales; relleno por defecto de elementos 8 px horizontal y 6 px vertical; el relleno por elemento se afina caso a caso con los valores de la tabla.

### 5.6 Bordes, elevación y esquinas

- Esquinas: 0 px en el nivel A (consecuencia del framework). En el nivel B, 8 px solo en imágenes (logotipo, botón principal).
- Bordes de tarjeta: 1 px `border-soft`. Bordes de campo: 1 px `border-input`; en foco, 2 px `accent-blue-600`.
- Sin sombras. La elevación se comunica con saltos de superficie: fondo `bg-app` → tarjeta `surface` → fila resaltada `surface-alt`.

### 5.7 Iconografía

- Un solo conjunto con trazo uniforme. Opciones de licencia permisiva a comprobar antes de elegir: Lucide (ISC), Phosphor (MIT) o Material Symbols (Apache 2.0).
- Tamaños: 16 px (en línea con texto), 20 px (botones), 24 px (estados). Exportar PNG en 1x y 2x; teñir con los tokens de texto y acento.
- Lista mínima: ojo, ojo tachado, carpeta, carpeta abierta, flecha derecha y abajo (plegado), lupa, check, alerta, información, cierre, descarga, cerrar sesión, actualizar.
- **No usar emoji** como iconos de interfaz. *(No verificado)* Tk en Windows suele mostrarlos en monocromo o como recuadros; verificarlo en tu equipo. Hoy el log usa `OK/SKIP/X/FMT` en ASCII por esa razón; el rediseño lo sustituye por iconos propios acompañados de texto.

### 5.8 Marca e imágenes

- **Logotipo:** una marca propia sencilla (flecha de descarga sobre un cuadrado de degradado azul→violeta), 40 px y 80 px. **No usar el logotipo institucional de UTP**: es una herramienta personal y no consta permiso para usar la marca.
- **Cabecera:** franja de 56 px con el degradado de marca (imagen 1x y 2x), logotipo, nombre de la aplicación y, a la derecha, el chip de sesión.
- **Icono de la aplicación:** `.ico` multitamaño (16, 24, 32, 48, 256 px) para la barra de tareas y la barra de título.
- **Ilustraciones:** una sola, opcional, para el estado vacío ("sin cursos"). Línea simple en azul y violeta pastel, 160×120 px.
- **Distribución:** incrustar los recursos en base64 en un módulo propio evita rutas de archivos al empaquetar con PyInstaller (tarea 2.6 del plan).
- **Spinner:** GIF animado de 24 px en `#4A5FE8` con fondo transparente, para el login y la carga de matrícula. Es la única animación del diseño.

---

## 6. Estructura de ventana y navegación

### 6.1 Ventana única

Una sola ventana con cuatro vistas intercambiables, de modo que el marco no salta. Mantener la barra de título nativa de Windows: el usuario pidió poder maximizar, minimizar y acoplar la ventana (Aero Snap), y una barra de título propia perdería esas funciones.

| Propiedad | Valor |
|---|---|
| Tamaño inicial | 1040 × 720 px |
| Tamaño mínimo | 860 × 600 px |
| Título | "UTP+class Downloader — Acceso / Cursos / Descarga / Resumen" |
| Posición | Centrada en la primera apertura; se conserva entre vistas |
| Ancho máximo del contenido | 960 px, centrado, para que no se estire en pantallas anchas |

**Alternativa mínima** si no se adopta la ventana única: tres ventanas con el mismo tamaño, la misma posición, la misma cabecera y el mismo patrón de título.

### 6.2 Marco persistente

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [marca] UTP+class Downloader      ● Acceso ─ ○ Cursos ─ ○ Descarga ─ ○ Resumen      [sesión] │  ← cabecera 56 px
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                        área de contenido (bg-app)                        │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│ v3.1.0-alpha.1                                              estado breve │  ← pie 32 px
└──────────────────────────────────────────────────────────────────────────┘
```

- **Indicador de pasos:** cuatro nodos conectados por una línea. Completado: círculo `accent-violet-600` con check. Actual: círculo `accent-blue-600` con número y etiqueta en semibold. Pendiente: círculo `border-soft` con número en `text-disabled`. Los pasos completados **no son clicables** salvo "Cursos" desde "Resumen" (acción "Volver a cursos").
- **Chip de sesión** (a la derecha, visible tras el login): código de usuario y acción "Cerrar sesión". No muestra token ni nombre completo.
- **Pie:** versión a la izquierda; a la derecha, un mensaje breve de estado ("Listo", "Descargando…", "Sesión renovada").

---

## 7. Especificación de pantallas

### 7.1 Acceso

```
┌──────────────────────────────────────────────────────────────────┐
│  cabecera (sin sesión)                                           │
├──────────────────────────────────────────────────────────────────┤
│                       fondo #F5F4FF                              │
│                                                                  │
│             ┌────────────────────────────────────┐               │
│             │ [marca 40 px]                      │               │
│             │ Inicia sesión                      │  título 18 pt │
│             │ Usa tu código y clave de UTP+class │  ayuda 9 pt   │
│             │                                    │               │
│             │ Código de usuario                  │               │
│             │ [______________________________]   │  campo 36 px  │
│             │                                    │               │
│             │ Contraseña                         │               │
│             │ [_________________________] [ojo]  │               │
│             │                                    │               │
│             │ ┌ mensaje (espacio reservado) ──┐  │               │
│             │ └───────────────────────────────┘  │               │
│             │ [            Entrar              ] │  botón 40 px  │
│             │                                    │               │
│             │ [candado] Tu clave no se guarda.   │  ayuda 9 pt   │
│             └────────────────────────────────────┘               │
├──────────────────────────────────────────────────────────────────┤
│ v3.1.0-alpha.1                                      Sin sesión   │
└──────────────────────────────────────────────────────────────────┘
```

**Medidas:** tarjeta de 400 px de ancho, centrada horizontal y verticalmente (con espacio flexible arriba y abajo); relleno interno 24 px; etiqueta → campo 4 px; campo → siguiente etiqueta 16 px; mensaje → botón 12 px.

**Comportamiento**
- Foco inicial en el código. Tab recorre código → contraseña → ojo → Entrar.
- Enter en cualquier campo envía el formulario; Escape no cierra la aplicación.
- El ojo alterna entre ocultar y mostrar la contraseña; por defecto oculta.
- Durante la autenticación: botón deshabilitado con el texto "Autenticando…", spinner a la izquierda del mensaje y campos de solo lectura.
- **Mensaje reservado:** el espacio de 40 px existe siempre, para que el formulario no cambie de altura al aparecer un error.
- Error de credenciales: banner `error` con icono y texto; no se reintenta automáticamente (ADR-0001) y el texto lo dice.
- La contraseña nunca se rellena automáticamente ni se conserva tras un fallo, salvo el código de usuario.
- *(Opcional, requiere decisión)* "Recordar mi código": guardaría solo el código de usuario, que según la regla vigente del repo no es un secreto; la contraseña y el token nunca.

### 7.2 Cursos (selección)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ cabecera + pasos (2 de 4)                                    [sesión]    │
├──────────────────────────────────────────────────────────────────────────┤
│  Tus cursos                                              [Actualizar]    │
│  Elige qué descargar. Se pre-marca el ciclo vigente.                     │
│                                                                          │
│  [lupa] Buscar curso…                                                    │
│                                                                          │
│ ┌─ ▾ 2026 - Ciclo 2 Agosto PREG (001)  [vigente]  8 cursos  Seleccionar todo ─┐
│ │  ☑ Mecánica clásica                                       Clase 41509      │
│ │  ☑ Cálculo I                                              Clase 33994      │
│ │  ☐ …                                                                         │
│ └────────────────────────────────────────────────────────────────────────────┘
│ ┌─ ▸ Ciclos anteriores · 3 ciclos · 21 cursos ───────────────────────────────┐
│ └────────────────────────────────────────────────────────────────────────────┘
│ ┌─ ▸ Otros (sin ciclo) · 2 cursos ───────────────────────────────────────────┐
│ └────────────────────────────────────────────────────────────────────────────┘
│  [aviso] 0 cursos excluidos                                              │
├──────────────────────────────────────────────────────────────────────────┤
│ Destino  [carpeta] C:\…\descargas_utp   [Cambiar]     8 seleccionados    │
│                                              [ Descargar 8 cursos ]      │  ← barra de acción fija
└──────────────────────────────────────────────────────────────────────────┘
```

**Estructura**
- **Zona desplazable** con los grupos; la **barra de acción inferior queda fija** (destino, contador y botón principal siempre visibles). La barra de desplazamiento usa los colores del tema (`sbar_*`): pista `#EEF0FF`, control `#C7C4EC`, flechas `#5B5780`.
- **Acordeón por ciclo:** vigente expandido; "Ciclos anteriores" plegado y contiene, dentro, un acordeón por cada ciclo; "Otros (sin ciclo)" plegado. El plegado cumple lo definido en el plan (Fase 4, tarea 4.1).
- **Cabecera de grupo** (fondo `surface-alt`, 40 px): flecha de plegado, nombre del ciclo en semibold, chip "vigente" (`accent-violet-100` / `accent-violet-700`), chip con el número de cursos y, a la derecha, el enlace "Seleccionar todo / Quitar todo" en `accent-blue-600`.
- **Fila de curso** (40 px de alto, separador de 1 px `border-soft`): casilla, nombre del curso (cuerpo 10 pt) y, a la derecha, metadatos en caption (`text-secondary`). Fila resaltada en `surface-alt` al pasar el ratón.
- **Metadatos:** el número de clase como texto gris. La modalidad (`P`, `R`, `VT`) **solo se muestra si se confirma su significado**; no se traduce por suposición.
- **Búsqueda:** filtra en vivo por nombre; los grupos sin coincidencias se ocultan; el contador de seleccionados no cambia al filtrar.
- **Barra de acción:** contador "N cursos seleccionados"; el botón cambia de texto ("Descargar 8 cursos") y se deshabilita con cero seleccionados, con la ayuda "Selecciona al menos un curso".
- **Destino:** icono de carpeta, ruta en Consolas 9 pt truncada con puntos suspensivos en el medio si no cabe, y botón secundario "Cambiar".
- **Cursos excluidos:** un aviso discreto (`aviso`) solo si el número es mayor que cero: "N cursos no se pueden descargar (sin identificador válido)".

**Estados**
- Carga de matrícula: spinner centrado con "Cargando tus cursos…".
- Error de matrícula: banner `error` con el motivo y botón "Reintentar" (sustituye el `PopupError`).
- Sin cursos: ilustración pequeña y "No tienes cursos matriculados este período."

### 7.3 Descarga (progreso)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ cabecera + pasos (3 de 4)                                    [sesión]    │
├──────────────────────────────────────────────────────────────────────────┤
│  Descargando                                                             │
│  ┌ Avance general ─────────────────────────────────────────────────────┐ │
│  │ Curso 2 de 5                                                  40 %  │ │
│  │ ████████████░░░░░░░░░░░░░░░░░░░░░░░░                                │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│  ┌ Curso actual ───────────────────────────────────────────────────────┐ │
│  │ Mecánica clásica                              62 %  (24 de 39 archivos) │
│  │ ██████████████████████░░░░░░░░░░░░░░                                │ │
│  │ Semana 07 · …/Video_HCJM.mp4                                        │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│  [✓ 24 Descargados]  [↷ 3 Ya existían]  [▫ 71 Filtrados]  [✕ 0 Errores] │
│  ┌ Detalle ────────────────────────────────────────────── [Ocultar] ──┐  │
│  │ log con color por línea (Consolas 9 pt)                            │  │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

**Elementos**
- **Avance general:** "Curso N de M", calculado en la GUI con el tamaño de la selección y los eventos de fin de curso (incluye los cursos que fallaron al cargar). No requiere cambios en `core`.
- **Curso actual:** nombre, porcentaje y "X de Y archivos" (con el total que da `course_started` y los eventos terminales). Barra de 12 px de alto, relleno `accent-blue-600`, pista `#E3E6FA`.
- **Línea del archivo en curso:** semana y nombre, truncado por el medio si es largo, con tooltip con el texto completo.
- **Contadores:** cuatro chips con los mismos nombres que la TUI. Éxito `#DDF6EA`/`#14693F`, aviso `#FFF1D6`/`#8A5300`, información `#DCE4FF`/`#2F3FB8`, error `#FFE1E6`/`#B4233F`; cada uno con icono y cifra en semibold. Los chips con valor cero se atenúan.
- **Detalle (log):** una línea por evento terminal, con color de texto según estado y un prefijo de icono más la palabra ("Descargado", "Ya existía", "Filtrado", "Error"). Fondo `surface-alt`, desplazamiento automático, máximo recomendado de líneas visibles configurable. Se puede ocultar para dar más espacio a las tarjetas.
- **Cancelar:** **no se muestra** hasta que exista la cancelación real (Tareas 2.3 y 2.4). Cuando exista: botón secundario con borde de error (`#B4233F`) a la derecha del encabezado, con diálogo de confirmación "¿Cancelar la descarga? Lo ya descargado se conserva."
- **Cerrar la ventana durante la descarga:** diálogo "Hay una descarga en curso. ¿Salir de todos modos?" con "Seguir descargando" como acción por defecto.

### 7.4 Resumen

```
┌──────────────────────────────────────────────────────────────────────────┐
│ cabecera + pasos (4 de 4)                                    [sesión]    │
├──────────────────────────────────────────────────────────────────────────┤
│  [check grande]  Descarga completada                                     │
│  5 cursos procesados                                                     │
│                                                                          │
│  ┌ 24 ──────┐ ┌ 3 ───────┐ ┌ 71 ──────┐ ┌ 0 ───────┐                     │
│  │Descargados│ │Ya existían│ │Filtrados │ │ Errores  │                     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                     │
│                                                                          │
│  Carpeta  C:\…\descargas_utp                                             │
│                                                                          │
│  [ Abrir carpeta ]   [ Volver a cursos ]                      [ Salir ]  │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Cabecera de resultado** según el caso: sin errores, icono de check en `accent-violet-600` y "Descarga completada"; con errores, icono de aviso y "Descarga completada con errores"; si hubo cancelación (cuando exista), "Descarga cancelada".
- **Cuatro tarjetas de cifras** (cifra 22 pt semibold, etiqueta 9 pt), con los colores de estado de la sección 5.1; ancho igual, separación 16 px.
- **Errores:** si el número es mayor que cero, un bloque desplegable "Ver errores" con la lista de archivos y el motivo; no se incluye "reintentar" hasta que exista esa función.
- **Acciones:** "Abrir carpeta" (principal), "Volver a cursos" (secundario, vuelve a la selección conservando la sesión) y "Salir" (texto, sin relleno).

### 7.5 Estados transversales

| Situación | Presentación |
|---|---|
| Sesión a punto de caducar (token de 24 h) | Chip de sesión en tono `aviso`; mensaje en el pie. |
| Sesión renovada automáticamente | Entrada informativa en el log y mensaje breve en el pie ("Sesión renovada"). |
| Sesión expirada (401) | Diálogo "Tu sesión expiró. Inicia sesión de nuevo; lo ya descargado se conserva." y vuelta al Acceso. |
| Curso sin contenido disponible (403/404) | Línea de error en el log "contenido no disponible" y el curso cuenta como terminado con error; la descarga sigue con el siguiente. |
| Falta de Chromium | No aplica al login actual, que ya no usa navegador (ADR-0007). |
| Sin conexión | Banner `error`: "No se pudo conectar. Revisa tu conexión e inténtalo de nuevo." con botón de reintento. |

---

## 8. Biblioteca de componentes

### 8.1 Botones

| Variante | Fondo | Texto | Borde | Hover | Uso |
|---|---|---|---|---|---|
| Principal | `#4A5FE8` | Blanco | — | `#3F52D6` | Una por pantalla (Entrar, Descargar, Abrir carpeta) |
| Secundario | Blanco | `#4A5FE8` | 1 px `#4A5FE8` | Fondo `#EEF0FF` | Cambiar, Actualizar, Volver |
| Texto | Transparente | `#4A5FE8` | — | Subrayado | Seleccionar todo, Salir |
| Peligro (secundario) | Blanco | `#B4233F` | 1 px `#B4233F` | Fondo `#FFE1E6` | Cancelar descarga |
| Deshabilitado | `#DAD8F5` | `#9C99BE` | — | — | Cualquier botón inactivo |

Medidas: alto 40 px (principal) y 32 px (secundario y texto); relleno horizontal 16 px; texto 10 pt semibold; el principal del login ocupa todo el ancho de la tarjeta; separación entre botones 12 px; área mínima de clic 32 px.

### 8.2 Campos de entrada

Alto 36 px; fondo blanco; borde 1 px `#8D8ABF`; texto 10 pt `text-primary`; marcador de posición en `text-disabled`; en foco, borde 2 px `#4A5FE8`; en error, borde `#B4233F` con texto de ayuda en el mismo color y su icono. Etiqueta siempre **encima** del campo, nunca como marcador de posición único. *(No verificado)* Controlar el grosor del anillo de foco puede requerir acceso directo al widget Tk tras `finalize`, porque el framework no lo expone como parámetro; si resulta frágil, usar solo el cambio de color del borde.

### 8.3 Casillas

Casilla de 20 px con borde `#8D8ABF` y marca en `#4A5FE8`; texto a 8 px de la casilla; la fila completa responde al clic. La casilla estándar de Tk es la parte más débil visualmente: si el resultado no convence, sustituirla por dos imágenes (marcada y sin marcar) del nivel B.

### 8.4 Chips y etiquetas

Alto 24 px, relleno horizontal 8 px, texto 9 pt semibold, fondo suave y texto profundo de la misma familia (sección 5.1). Se usan para "vigente", contadores de cursos y los cuatro estados.

### 8.5 Presentación de nombres de curso

La plataforma devuelve los nombres en mayúsculas. Opción recomendada: **solo para mostrar**, convertir a tipo oración con una lista de excepciones (siglas como TIC, numerales romanos como II y III). La carpeta de descarga y la identidad del curso siguen usando el valor original. Riesgo: errores en siglas no previstas; si molestan, dejar el texto original. Probar con nombres de más de 50 caracteres (por ejemplo, "HERRAMIENTAS INFORMÁTICAS PARA LA TOMA DE DECISIONES") para comprobar el truncado.

### 8.6 Tarjetas y banners

- **Tarjeta:** fondo blanco, borde 1 px `border-soft`, relleno 16 px, separación entre tarjetas 16 px.
- **Banner:** fondo y texto del estado correspondiente, icono de 20 px a la izquierda, relleno 12 px, texto de una o dos líneas.

### 8.7 Log

Fondo `#EEF0FF`, Consolas 9 pt, sin borde interno, relleno 8 px. Colores de texto por estado: éxito `#14693F`, aviso `#8A5300`, información `#2F3FB8`, error `#B4233F`. Cada línea lleva icono y palabra de estado para no depender del color.

### 8.8 Barras de progreso

Alto 12 px; relleno `#4A5FE8`; pista `#E3E6FA`; sin borde. El porcentaje se muestra como texto junto a la barra, no dentro de ella. Si el total es cero se muestra una barra indeterminada o el texto "Sin archivos", nunca una barra en 100 %.

---

## 9. Microcopy

Español neutro, tuteo, frases cortas, sin tecnicismos ni nombres internos de tareas.

| Contexto | Texto |
|---|---|
| Título del login | Inicia sesión |
| Ayuda del login | Usa tu código y clave de UTP+class |
| Etiquetas | Código de usuario · Contraseña |
| Botón de login | Entrar · Autenticando… |
| Nota de privacidad | Tu contraseña no se guarda. Solo se accede a tus propios cursos. |
| Credenciales inválidas | Código o contraseña incorrectos. No se reintentará automáticamente para evitar bloquear tu cuenta. |
| Campos vacíos | Completa tu código y tu contraseña. |
| Sin conexión | No se pudo conectar. Revisa tu conexión e inténtalo de nuevo. |
| Título de selección | Tus cursos |
| Ayuda de selección | Elige qué descargar. Se pre-marca el ciclo vigente. |
| Botón principal | Descargar N cursos |
| Cero seleccionados | Selecciona al menos un curso. |
| Sin cursos | No tienes cursos matriculados este período. |
| Excluidos | N cursos no se pueden descargar (sin identificador válido). |
| Progreso general | Curso N de M |
| Curso sin contenido | El contenido de este curso ya no está disponible. |
| Confirmar salida | Hay una descarga en curso. ¿Salir de todos modos? |
| Confirmar cancelación | ¿Cancelar la descarga? Lo ya descargado se conserva. |
| Resumen | Descarga completada · Descarga completada con errores |
| Sesión expirada | Tu sesión expiró. Inicia sesión de nuevo; lo ya descargado se conserva. |

Los cuatro contadores usan siempre los mismos nombres que la TUI: **Descargados, Ya existían, Filtrados por formato, Errores**.

---

## 10. Accesibilidad

- **Contraste:** todos los textos cumplen 4,5:1 según la tabla de la sección 5.2; los pastel vivos de bajo contraste no llevan texto.
- **No solo color:** cada estado combina color, icono y palabra.
- **Teclado:** orden de tabulación lógico en cada vista; Enter envía el login; Escape cierra diálogos; la casilla y el botón de ojo son alcanzables con Tab; foco siempre visible. *(No verificado)* La compatibilidad de Tk con atajos con subrayado (Alt + letra) en estos botones debe probarse antes de prometerla.
- **Tamaños de clic:** mínimo 32 px de alto en cualquier control interactivo.
- **Tipografía:** cuerpo de 10 pt y nada por debajo de 9 pt.
- **Escalado de pantalla de Windows:** declarar la aplicación como consciente de DPI antes de crear la ventana; si no, a 125 % o 150 % el texto y las imágenes salen borrosos. Cuidado con aplicar a la vez un factor de escala propio, que duplicaría el aumento. *(No verificado)* Probar a 100, 125 y 150 %.
- **Lectores de pantalla:** Tk ofrece soporte muy limitado; no se promete compatibilidad completa. Si fuera un requisito, es un argumento a favor del nivel C (PySide6).
- **Movimiento:** una sola animación (spinner), sin parpadeos ni efectos.

---

## 11. Dependencias con el código y el plan

El diseño es mayormente de presentación, pero algunos elementos requieren trabajo previo o paralelo. Se listan sin implementarlos.

| # | Elemento del diseño | Requiere | Dónde |
|---|---|---|---|
| D1 | Estado de carga real en el login | Llamar a `login()` en un hilo en vez de en el bucle de eventos | `ui_gui` |
| D2 | Aviso de cursos excluidos | Conservar el segundo valor que devuelve `group_courses_by_period` | `ui_gui` |
| D3 | Progreso global "Curso N de M" | Contar eventos de fin de curso y de error de curso en la GUI | `ui_gui` |
| D4 | Botón Cancelar y confirmación de salida seguros | Descarga atómica `.part` (tarea 2.3) y cancelación (tarea 2.4); sin ellas, cancelar deja archivos parciales | `downloader`, `core` |
| D5 | Avance de cada curso en la plataforma (`progress`) como metadato opcional en la fila | Añadir `progress` al registro normalizado y actualizar la prueba que fija sus claves exactas | `core`, `tests` |
| D6 | "Abrir carpeta" | Llamada al sistema operativo para abrir la ruta | `ui_gui` |
| D7 | Marca, iconos, spinner y cabecera | Módulo de recursos incrustados en base64 | nuevo módulo de recursos |
| D8 | Reintento tras sesión caducada | Usar `auth.refresh` para renovar la sesión sin pedir la clave | `auth`, `ui_gui` |
| D9 | Licencia | Corregir el ADR-0006 (LGPLv3+, no MIT) antes de cerrarlo | documentación |

---

## 12. Plan de implementación del rediseño

El orden va de lo que más cambia la percepción a lo que pule. Cada fase deja la aplicación funcionando.

| Fase | Contenido | Resultado visible |
|---|---|---|
| **D0 — Fundamentos** | Tokens de color, tipografía y espaciado en un único lugar; tema de FreeSimpleGUI con la paleta; fuente corregida; declaración de DPI; icono de ventana. | Toda la aplicación adopta colores y fuente coherentes sin cambiar el flujo. |
| **D1 — Marco y Acceso** | Ventana única con cabecera, pasos y pie; vista de login con tarjeta, ojo, Enter, mensaje reservado y estado de carga. | Primera impresión profesional. |
| **D2 — Cursos** | Acordeón por ciclo, cabeceras con chips, filas limpias, búsqueda, barra de acción fija con destino y contador, aviso de excluidos, estados de carga/error/vacío. | La pantalla más usada deja de ser una lista plana. |
| **D3 — Descarga y Resumen** | Avance general y por curso, contadores, log con color, confirmación de salida; vista de resumen con tarjetas de cifras. | Cierre del flujo con mejor retroalimentación. |
| **D4 — Pulido** | Iconos propios, spinner, ilustración del estado vacío, casillas con imagen si hace falta, revisión a 100/125/150 % de escala, recorrido solo con teclado. | Aspecto final y accesibilidad verificada. |

**Cuando existan las tareas 2.3 y 2.4:** añadir el botón Cancelar y su confirmación (D4 de la tabla de dependencias).

---

## 13. Criterios de aceptación y QA visual

| Área | Criterio |
|---|---|
| Coherencia | Las cuatro vistas comparten cabecera, pie, paleta, tipografía y patrón de título. |
| Estabilidad | El marco no cambia de tamaño ni de posición al pasar de una vista a otra; el formulario de login no salta cuando aparece un error. |
| Contraste | Todas las combinaciones de la sección 5.2 verificadas con una herramienta, sin excepciones en texto. |
| Teclado | Todo el flujo (login → selección → descarga → resumen) se completa sin ratón; el foco siempre es visible. |
| Escalado | Aspecto correcto a 100, 125 y 150 % de escala de Windows, sin texto cortado ni imágenes borrosas. |
| Tamaños | Utilizable en el tamaño mínimo (860 × 600) y al maximizar (contenido centrado, máximo 960 px). |
| Contenido real | Lista de 31 cursos en 5 ciclos sin lentitud; nombres de más de 50 caracteres truncados correctamente; 0, 1 y 31 cursos seleccionados. |
| Estados | Carga, error de login, error de matrícula, sin cursos, curso sin contenido, sesión expirada y salida durante la descarga, todos con su presentación definida. |
| Seguridad | Ninguna pantalla, log ni mensaje muestra la contraseña, el token ni fragmentos de ellos. |
| Consistencia con la TUI | Los cuatro contadores y sus nombres coinciden con los de la interfaz de terminal. |

---

## 14. Riesgos y decisiones abiertas

| Riesgo o decisión | Detalle | Propuesta |
|---|---|---|
| **Licencia de FreeSimpleGUI** | Los metadatos del paquete 5.1.0 declaran **LGPLv3+**; el ADR-0006 dice MIT. | Corregir el ADR antes de cerrarlo. La LGPL permite usar la biblioteca desde una aplicación propia, pero al empaquetar con PyInstaller conviene un formato que permita sustituirla y conservar el aviso de licencia. No soy abogado: confirmar las obligaciones antes de distribuir. |
| Techo visual del framework | Sin esquinas redondeadas, sombras ni degradados nativos. | Aplicar nivel A + recursos del nivel B; reevaluar PySide6 (nivel C) tras ver el resultado. Decisión del ADR-0006. |
| Ventana única | Requiere reorganizar `ui_gui.py` en vistas intercambiables. | Si se prefiere no refactorizar, usar la alternativa mínima de tres ventanas iguales. |
| Nombres de curso en tipo oración | Puede alterar siglas. | Función opcional con lista de excepciones; si molesta, mostrar el texto original. |
| Recordar el código de usuario | Guarda un dato personal en disco, aunque no secreto según la regla del repo. | Dejarlo fuera de la v1 salvo decisión expresa. |
| Modalidad (`P`, `R`, `VT`) | Se desconoce su significado exacto. | No mostrarla ni traducirla hasta confirmarlo. |
| Marca visual | No usar el logotipo de UTP. | Marca propia neutra. |
| Cancelación sin descarga atómica | Cancelar o cerrar durante una descarga deja archivos parciales que la siguiente ejecución da por completos. | No mostrar Cancelar hasta cerrar las tareas 2.3 y 2.4; confirmar siempre la salida. |
| Verificaciones pendientes en tu equipo | Resolución de `Segoe UI Semibold`, emoji en Tk, atajos con subrayado, comportamiento a 125 % y 150 %, anillo de foco. | Comprobarlas al inicio de D0 y D4; ajustar el diseño según el resultado. |

---

### Qué verifiqué y qué no

**Verificado:** que FreeSimpleGUI 5.1.0 ofrece los parámetros de estilo usados en este plan (lectura estática del código fuente); que su licencia declarada es LGPLv3+; las observaciones de la sección 2 sobre `ui_gui.py`.
**No verificado (marcado en el texto):** la apariencia real en tu pantalla, la resolución de las fuentes, el comportamiento a distintos factores de escala, el soporte de emoji y de atajos con subrayado en Tk, y los valores de contraste, calculados a mano.
