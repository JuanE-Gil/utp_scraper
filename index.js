const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  ImageRun, PageBreak, TableOfContents, LevelFormat, Header, Footer,
  PageNumber, NumberFormat, VerticalAlign, convertInchesToTwip
} = require("docx");

// ---------- Utilidades ----------
const FONT_BODY = "Calibri";
const FONT_CODE = "Consolas";
const COLOR_PRIMARY = "1F4E79";
const COLOR_ACCENT = "2E75B6";
const COLOR_MUTED = "595959";

function h1(text) {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
  });
}
function h2(text) {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300, after: 150 },
  });
}
function h3(text) {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 100 },
  });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160, line: 276 },
    children: [new TextRun({ text, font: FONT_BODY, size: 22, ...opts })],
  });
}
function pRich(runs, opts = {}) {
  return new Paragraph({
    spacing: { after: 160, line: 276 },
    children: runs,
    ...opts,
  });
}
function bullet(text, level = 0) {
  return new Paragraph({
    text,
    bullet: { level },
    spacing: { after: 90 },
    children: undefined,
  });
}
function bulletRich(runs, level = 0) {
  return new Paragraph({
    bullet: { level },
    spacing: { after: 90 },
    children: runs,
  });
}
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 300 },
    children: [new TextRun({ text, italics: true, size: 19, color: COLOR_MUTED, font: FONT_BODY })],
  });
}
function imageParagraph(path, width, height) {
  const data = fs.readFileSync(path);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 100 },
    children: [
      new ImageRun({
        data,
        transformation: { width, height },
        type: path.endsWith(".png") ? "png" : "jpg",
      }),
    ],
  });
}

function cell(text, opts = {}) {
  return new TableCell({
    width: opts.width || { size: 25, type: WidthType.PERCENTAGE },
    shading: opts.header ? { type: ShadingType.CLEAR, fill: COLOR_PRIMARY } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [
      new Paragraph({
        children: [
          new TextRun({
            text,
            bold: !!opts.header,
            color: opts.header ? "FFFFFF" : "000000",
            size: opts.size || 20,
            font: FONT_BODY,
          }),
        ],
      }),
    ],
  });
}

function makeTable(headerRow, rows, widths) {
  const wPct = widths || headerRow.map(() => Math.floor(100 / headerRow.length));
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: wPct.map((w) => w * 90),
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" },
      left: { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" },
      right: { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: "D9D9D9" },
      insideVertical: { style: BorderStyle.SINGLE, size: 2, color: "D9D9D9" },
    },
    rows: [
      new TableRow({
        tableHeader: true,
        children: headerRow.map((t, i) => cell(t, { header: true, width: { size: wPct[i], type: WidthType.PERCENTAGE } })),
      }),
      ...rows.map(
        (r) =>
          new TableRow({
            children: r.map((t, i) => cell(t, { width: { size: wPct[i], type: WidthType.PERCENTAGE } })),
          })
      ),
    ],
  });
}

function codeBlock(lines) {
  return lines.map(
    (line) =>
      new Paragraph({
        shading: { type: ShadingType.CLEAR, fill: "F5F5F5" },
        spacing: { after: 0, line: 240 },
        children: [
          new TextRun({
            text: line.length ? line : " ",
            font: FONT_CODE,
            size: 15,
            color: "1B1B1B",
          }),
        ],
      })
  );
}

// ---------- Cargar código fuente completo ----------
const scriptPath = "./utp_scraper_v2.2.py";
const scriptLines = fs.readFileSync(scriptPath, "utf-8").split("\n");

// ---------- Portada ----------
const coverPage = [
  new Paragraph({ text: "", spacing: { before: 1600 } }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "INFORME TÉCNICO DE PROYECTO", bold: true, size: 32, color: COLOR_PRIMARY, font: FONT_BODY })],
    spacing: { after: 200 },
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({
        text: "UTP+class Material Downloader",
        bold: true,
        size: 48,
        color: COLOR_ACCENT,
        font: FONT_BODY,
      }),
    ],
    spacing: { after: 100 },
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [
      new TextRun({
        text: "Herramienta de descarga masiva y organizada de materiales académicos",
        italics: true,
        size: 24,
        color: COLOR_MUTED,
        font: FONT_BODY,
      }),
    ],
    spacing: { after: 900 },
  }),
  imageParagraph("./diagrams/tui_mockup.png", 420, 298),
  new Paragraph({ text: "", spacing: { before: 900 } }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Versión del documento: 1.0", size: 20, font: FONT_BODY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Versión del script: utp_scraper_v2.py", size: 20, font: FONT_BODY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Fecha: 25 de septiembre de 2026", size: 20, font: FONT_BODY })],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- Tabla de contenidos ----------
const tocSection = [
  h1("Tabla de contenidos"),
  new TableOfContents("Tabla de contenidos", {
    hyperlink: true,
    headingStyleRange: "1-3",
  }),
  p("Nota: en Word, haz clic derecho sobre la tabla de contenidos y selecciona “Actualizar campos” para que se generen los números de página."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 1. Introducción ----------
const introSection = [
  h1("1. Introducción"),
  h2("1.1 Contexto y motivación"),
  p(
    "UTP+class es la plataforma de aprendizaje virtual utilizada por la Universidad Tecnológica del Perú (UTP). Cada curso publica materiales de estudio en múltiples formatos (PDF, video MP4, audio MP3, documentos DOCX) distribuidos en decenas de temas a lo largo del ciclo académico. Descargar manualmente cada archivo, curso por curso y semana por semana, es una tarea repetitiva y propensa a omisiones."
  ),
  p(
    "Este proyecto documenta el diseño y funcionamiento de un script en Python que automatiza dicha descarga, apoyándose en la misma API REST interna que consume el frontend de UTP+class, y presenta el resultado mediante una interfaz visual en la terminal (TUI) inspirada en herramientas como lazygit o lazydocker."
  ),
  h2("1.2 Objetivos"),
  bullet("Automatizar la descarga de todos los materiales descargables (PDF, MP4, DOCX, XLSX, PPTX, imágenes) de uno o varios cursos matriculados."),
  bullet("Organizar los archivos descargados en una estructura de carpetas coherente por curso, semana y tema."),
  bullet("Evitar la duplicación de contenido cuando un mismo material se ofrece en varios formatos redundantes (p. ej. video + solo-audio del mismo video)."),
  bullet("Filtrar elementos ajenos al material académico (íconos de interfaz, recursos decorativos) que técnicamente cumplen el patrón de una URL de archivo pero no son contenido del curso."),
  bullet("Ofrecer retroalimentación visual clara y en tiempo real del progreso de la descarga."),
  h2("1.3 Alcance"),
  p(
    "El script opera exclusivamente sobre cursos a los que el usuario ya tiene acceso legítimo como estudiante matriculado, reutilizando su propia sesión autenticada (token Bearer). No implementa mecanismos de evasión de autenticación, no automatiza el inicio de sesión, y no accede a contenido de otros estudiantes o docentes. Su uso está pensado para consumo personal (respaldo y estudio offline), no para redistribución pública del material."
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 2. Arquitectura ----------
const archSection = [
  h1("2. Arquitectura del sistema"),
  p(
    "El sistema se compone de cinco actores principales: el usuario (que provee credenciales de sesión extraídas manualmente del navegador), el script Python que orquesta todo el proceso, la API REST de UTP+class (que expone la estructura del curso en formato JSON), el almacenamiento de archivos en Amazon S3 (donde residen los binarios reales), y el sistema de archivos local donde se organiza la descarga."
  ),
  imageParagraph("./diagrams/architecture.png", 580, 141),
  caption("Figura 1. Arquitectura general del sistema y flujo de comunicación entre componentes."),
  h2("2.1 Componentes"),
  makeTable(
    ["Componente", "Responsabilidad"],
    [
      ["Usuario / Navegador", "Provee el token de sesión (JWT Bearer), user-id y tenant-id extraídos vía DevTools; no requiere automatización del login."],
      ["Script Python (utp_scraper_v2.py)", "Orquesta las llamadas a la API, parsea la estructura del curso, filtra y descarga los archivos, y renderiza la interfaz visual."],
      ["API UTP+class (api-pao.utpxpedition.com)", "Expone el endpoint GET /course/student/courses/{courseId}/sections/{sectionId}/full con la estructura completa del curso en JSON."],
      ["Almacenamiento S3 (utp-prd-upload-file-storage)", "Aloja los archivos binarios reales (PDF, MP4, MP3, DOCX, etc.) referenciados dentro del JSON de la API."],
      ["Sistema de archivos local", "Destino final de la descarga, organizado jerárquicamente por curso, semana y tema."],
      ["Interfaz visual (rich)", "Renderiza en tiempo real el estado del proceso: curso actual, progreso, registro de eventos y contadores."],
    ],
    [30, 70]
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 3. Flujo de datos ----------
const flowSection = [
  h1("3. Flujo de datos y lógica de negocio"),
  p(
    "El proceso de descarga sigue un pipeline secuencial por cada curso configurado. La figura 2 detalla la lógica completa, incluyendo los dos puntos de decisión que resuelven los dos problemas identificados durante el desarrollo: materiales duplicados en varios formatos, y elementos que no son material académico (íconos de interfaz)."
  ),
  imageParagraph("./diagrams/dataflow.png", 380, 678),
  caption("Figura 2. Diagrama de flujo del proceso de extracción y descarga."),
  h2("3.1 Tipos de contenido en la API"),
  p("Cada 'tema' (theme) de un curso contiene una lista de 'contenidos' (contents), cada uno con un campo type que determina cómo se extraen sus archivos:"),
  makeTable(
    ["Tipo (type)", "Origen del archivo", "Tratamiento"],
    [
      ["FILE", "metadata.url (enlace directo a S3)", "Se descarga directamente."],
      ["HTML", "metadata.contentHtml (HTML embebido con enlaces \"Descargar .MP4/.MP3/.PDF\")", "Se extraen las URLs con expresión regular filtrada por dominio S3."],
      ["HOMEWORK / EVALUATION", "description (HTML con adjuntos, ej. plantillas de ejercicios)", "Se extraen las URLs con la misma expresión regular."],
      ["URL", "metadata.url (enlace externo: biblioteca virtual, YouTube, etc.)", "Se ignora; no es material propio de UTP descargable."],
      ["FORUM", "No aplica (actividad de participación, sin archivo adjunto directo)", "Se ignora."],
    ],
    [20, 45, 35]
  ),
];

// ---------- 4. Deduplicación y filtrado ----------
const dedupSection = [
  h1("4. Deduplicación de formatos y filtrado de ruido"),
  h2("4.1 Problema: materiales repetidos en múltiples formatos"),
  p(
    "Cada contenido de tipo \"Video demostrativo\" en UTP+class ofrece tres enlaces de descarga para el mismo material: el video (.mp4), una versión de solo audio del mismo video (.mp3) y una transcripción en PDF del guion (.pdf). Descargar los tres implica guardar el mismo contenido dos veces (video y su propio audio)."
  ),
  h3("Solución implementada"),
  p(
    "Se introdujo el conjunto configurable DOWNLOAD_EXTENSIONS, que actúa como lista blanca de formatos a conservar. Por defecto excluye \"mp3\", ya que su contenido de audio está contenido dentro del \"mp4\" correspondiente:"
  ),
  ...codeBlock([
    'DOWNLOAD_EXTENSIONS = {"pdf", "mp4", "docx", "xlsx", "pptx", "png", "jpg", "jpeg"}',
    "# mp3 excluido por defecto -> es el mismo audio que ya viene en el mp4",
  ]),
  p("Cada URL candidata se valida contra este conjunto antes de intentar la descarga; si su extensión no está incluida, se contabiliza en skipped_format y se omite."),
  h2("4.2 Problema: íconos de interfaz confundidos con material"),
  p(
    "La primera versión del extractor de enlaces aceptaba cualquier URL que terminara en una extensión de archivo reconocida (.pdf, .mp4, .png, etc.), sin restricción de dominio. Esto causó que íconos decorativos de la interfaz de UTP+class (ej. alert-circle-white_GSYBSA.png, file-text_IMHXIJ.png, film_ABBHVE.png, link-2_RXQOTJ.png, music_ZKQWEM.png) —servidos desde un CDN de íconos ajeno al contenido académico— se descargaran junto con el material real."
  ),
  h3("Solución implementada"),
  p(
    "Se verificó que, en la estructura de datos de la API, todo archivo real de un curso se sirve siempre desde el mismo bucket de almacenamiento: utp-prd-upload-file-storage.s3.amazonaws.com. La expresión regular de extracción se restringió a ese dominio exacto:"
  ),
  ...codeBlock([
    'UTP_FILE_DOMAIN = "utp-prd-upload-file-storage.s3.amazonaws.com"',
    "FILE_EXT_RE = re.compile(",
    "    r'https?://' + re.escape(UTP_FILE_DOMAIN) + r'/[^\\s\"\\'<>]+?\\.(pdf|mp4|mp3|docx?|xlsx?|pptx?|png|jpe?g)',",
    "    re.IGNORECASE,",
    ")",
  ]),
  p("Con este cambio, cualquier URL de un dominio distinto (CDNs de íconos, avatares, recursos de terceros embebidos en el HTML) queda automáticamente excluida, sin necesidad de mantener listas negras de patrones de nombre."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 5. Interfaz visual ----------
const uiSection = [
  h1("5. Interfaz visual (TUI)"),
  p(
    "La interfaz se construye con la librería rich sobre un mecanismo de renderizado \"en el mismo lugar\" (Live, con screen=False), en vez de tomar control de pantalla completa. Esta decisión de diseño surgió tras detectar que el modo de pantalla completa (screen=True) no se renderiza correctamente en terminales embebidas dentro de aplicaciones de escritorio (IDEs, apps tipo Claude Code/Cowork), que no siempre reportan con precisión las dimensiones del terminal."
  ),
  imageParagraph("./diagrams/tui_mockup.png", 520, 370),
  caption("Figura 3. Composición de la interfaz visual: encabezado, panel de estado, panel de registro y pie con contadores."),
  h2("5.1 Elementos de la interfaz"),
  makeTable(
    ["Panel", "Contenido"],
    [
      ["Encabezado", "Título de la aplicación."],
      ["Estado", "Curso en proceso, barra de progreso del curso actual (archivos completados / total), semana y tema en curso, y nombre del archivo que se está descargando."],
      ["Registro", "Últimas 8 acciones realizadas, cada una marcada como éxito (verde), ya existente (amarillo) o error (rojo)."],
      ["Pie / contadores", "Totales acumulados de archivos descargados, ya existentes, filtrados por formato, y errores."],
    ],
    [25, 75]
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 6. Estructura de salida ----------
const outputSection = [
  h1("6. Estructura de la descarga en disco"),
  p(
    "Los archivos se organizan jerárquicamente replicando la estructura académica del curso: curso → semana → tema → archivo. Los nombres de carpeta se sanean (se eliminan tildes, caracteres no válidos para el sistema de archivos, y se recortan a una longitud máxima) mediante la función sanitize()."
  ),
  imageParagraph("./diagrams/folders.png", 560, 111),
  caption("Figura 4. Ejemplo de estructura de carpetas resultante."),
  h2("6.1 Idempotencia"),
  p(
    "Antes de descargar cada archivo, el script verifica si ya existe en el destino con tamaño mayor a cero. De ser así, se omite (skip_exist). Esto permite interrumpir la ejecución (por ejemplo, si el token expira a mitad de proceso) y volver a correr el script más tarde sin perder el trabajo ya realizado ni duplicar descargas."
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 7. Módulos y funciones ----------
const modulesSection = [
  h1("7. Módulos y funciones principales"),
  makeTable(
    ["Función", "Propósito"],
    [
      ["sanitize(name)", "Convierte un texto arbitrario (título de curso, tema o archivo) en un nombre válido y seguro para carpetas/archivos, removiendo tildes y caracteres reservados."],
      ["get_section_full(course_id, section_id)", "Llama al endpoint GET .../sections/{id}/full y devuelve el JSON con la estructura completa del curso."],
      ["extract_urls_from_html(html)", "Aplica la expresión regular restringida al dominio S3 sobre un bloque de HTML embebido y devuelve pares (url, extensión) únicos."],
      ["download_file(url, ext, dest_folder, fallback_name)", "Descarga un archivo por streaming, evitando redescargas si ya existe; devuelve el resultado (ok / skip_exist / error)."],
      ["text_progress_bar(done, total, width)", "Genera una barra de progreso en texto plano (bloques Unicode) usada dentro del panel de Estado."],
      ["build_view()", "Construye el conjunto de paneles (encabezado, estado, registro, pie) como un único renderable de rich."],
      ["process_course(course_name, course_id, section_id, live)", "Orquesta la descarga completa de un curso: obtiene la estructura, arma la lista de trabajos, filtra por formato, descarga y actualiza la interfaz en vivo."],
      ["main()", "Punto de entrada: valida configuración, inicializa Live y recorre la lista de cursos configurados."],
    ],
    [35, 65]
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 8. Configuración ----------
const configSection = [
  h1("8. Configuración y parametrización"),
  makeTable(
    ["Parámetro", "Descripción", "Valor por defecto"],
    [
      ["AUTH_TOKEN", "Token Bearer (JWT) de la sesión activa del usuario en class.utp.edu.pe. Expira aproximadamente a las 24 horas de haberse emitido.", "(debe rellenarse manualmente)"],
      ["USER_ID", "Identificador UUID del usuario dentro de la plataforma.", "(debe rellenarse manualmente)"],
      ["TENANT_ID", "Identificador UUID de la institución (UTP) usado como header x-tenant-id.", "(debe rellenarse manualmente)"],
      ["COURSES", "Lista de tuplas (nombre_carpeta, courseId, sectionId) a procesar.", "Lista vacía / ejemplo incluido"],
      ["OUTPUT_DIR", "Carpeta raíz donde se organiza toda la descarga.", "./descargas_utp"],
      ["DOWNLOAD_EXTENSIONS", "Conjunto de extensiones permitidas para descarga (lista blanca).", "pdf, mp4, docx, xlsx, pptx, png, jpg, jpeg"],
      ["UTP_FILE_DOMAIN", "Dominio S3 al que se restringe la extracción de enlaces, para excluir íconos u otros recursos ajenos.", "utp-prd-upload-file-storage.s3.amazonaws.com"],
    ],
    [22, 58, 20]
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 9. Seguridad ----------
const securitySection = [
  h1("9. Seguridad y manejo de credenciales"),
  bullet("El AUTH_TOKEN es un JWT que representa la sesión personal del usuario; equivale a la contraseña mientras esté vigente. No debe compartirse, publicarse en repositorios, ni pegarse en chats o servicios externos."),
  bullet("El token tiene una vida útil corta (≈24 horas). Si expira a mitad de una ejecución larga, las siguientes peticiones fallarán; basta con regenerarlo y volver a correr el script, ya que la idempotencia evita redescargas."),
  bullet("El script no automatiza el inicio de sesión ni almacena la contraseña del usuario en ningún momento; solo reutiliza una sesión ya iniciada manualmente por el navegador."),
  bullet("Se recomienda no dejar el token con valores reales en un archivo versionado en control de código (git); considerar variables de entorno para usos recurrentes."),
  bullet("Ante cualquier sospecha de exposición del token, cerrar sesión en class.utp.edu.pe invalida la sesión y, por lo tanto, el token."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 10. Manejo de errores ----------
const errorsSection = [
  h1("10. Manejo de errores y resiliencia"),
  makeTable(
    ["Escenario", "Comportamiento del script"],
    [
      ["Token expirado o inválido", "La llamada a get_section_full() lanza una excepción HTTP; se registra el error en el panel de Registro y se continúa con el siguiente curso configurado."],
      ["Archivo ya descargado previamente", "Se detecta por presencia y tamaño > 0 en el destino; se omite sin volver a transferir datos (skip_exist)."],
      ["Fallo de red durante la descarga de un archivo puntual", "Se captura la excepción, se registra como error y se continúa con el siguiente archivo, sin detener el proceso completo."],
      ["Formato no deseado (lista blanca)", "Se descarta silenciosamente y se contabiliza en el contador de \"filtrados por formato\"."],
      ["Interrupción manual (Ctrl+C) a mitad de proceso", "Los archivos ya escritos permanecen en disco; una nueva ejecución los detecta como existentes y continúa desde donde quedó."],
    ],
    [30, 70]
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 11. Instalación y uso ----------
const usageSection = [
  h1("11. Requisitos, instalación y guía de uso"),
  h2("11.1 Requisitos"),
  bullet("Python 3.8 o superior."),
  bullet("Librerías: requests, rich."),
  h2("11.2 Instalación"),
  ...codeBlock(["pip install requests rich --break-system-packages"]),
  h2("11.3 Obtención de credenciales"),
  bullet("Abrir class.utp.edu.pe e iniciar sesión normalmente."),
  bullet("Entrar a cualquier curso y abrir las herramientas de desarrollador del navegador (tecla F12)."),
  bullet("En la pestaña Network (Red), filtrar por Fetch/XHR."),
  bullet("Seleccionar cualquier petición hacia api-pao.utpxpedition.com y revisar sus cabeceras (Headers)."),
  bullet("Copiar los valores de authorization (sin la palabra \"Bearer\"), user-id y x-tenant-id."),
  h2("11.4 Obtención de identificadores de curso"),
  bullet("Desde \"Mis cursos\", entrar a cada curso."),
  bullet("Extraer courseId y sectionId directamente de la URL del navegador: class.utp.edu.pe/student/courses/{courseId}/section/{sectionId}/..."),
  h2("11.5 Ejecución"),
  ...codeBlock(["python utp_scraper_v2.py"]),
  p("El script mostrará la interfaz visual descrita en la sección 5, procesando cada curso configurado en la lista COURSES en orden secuencial."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 12. Limitaciones y trabajo futuro ----------
const futureSection = [
  h1("12. Limitaciones y trabajo futuro"),
  h2("12.1 Limitaciones actuales"),
  bullet("La lista de cursos (COURSES) debe completarse manualmente; no existe aún descubrimiento automático de todos los cursos matriculados del período."),
  bullet("El token debe renovarse manualmente si expira durante una ejecución muy larga."),
  bullet("Las descargas se realizan de forma secuencial (un archivo a la vez), priorizando no sobrecargar el servidor sobre la velocidad total."),
  bullet("No hay reintentos automáticos ante fallos de red transitorios dentro de la misma ejecución."),
  h2("12.2 Mejoras propuestas"),
  bullet("Integrar el endpoint de listado de cursos (\"Mis cursos\") para poblar COURSES automáticamente."),
  bullet("Añadir reintentos con backoff exponencial para descargas fallidas."),
  bullet("Detectar la expiración del token en tiempo real y solicitar uno nuevo sin reiniciar el proceso completo."),
  bullet("Paralelizar descargas dentro de límites razonables para acelerar el proceso sin saturar el servidor."),
  bullet("Exportar un reporte final en CSV/JSON con el detalle de cada archivo procesado."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 13. Consideraciones éticas y legales ----------
const ethicsSection = [
  h1("13. Consideraciones éticas y de uso responsable"),
  bullet("El script solo accede a contenido al que el usuario ya tiene acceso legítimo como estudiante matriculado, mediante su propia sesión autenticada."),
  bullet("Se recomienda uso estrictamente personal (estudio offline, respaldo); no se recomienda la redistribución pública del material descargado, dado que pertenece a la institución y a los autores originales del contenido."),
  bullet("El script incluye una breve pausa entre descargas (time.sleep) para evitar generar carga excesiva sobre la infraestructura de la universidad."),
  bullet("Se recomienda revisar el reglamento y los términos de uso de la plataforma antes de un uso extensivo o automatizado."),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- 14. Conclusiones ----------
const conclusionSection = [
  h1("14. Conclusiones"),
  p(
    "El script utp_scraper_v2.py resuelve de forma efectiva el problema de descarga masiva y organizada de materiales académicos en UTP+class, apoyándose directamente en la API REST interna de la plataforma en lugar de simular interacciones de navegador, lo que simplifica considerablemente su implementación y mantenimiento."
  ),
  p(
    "Durante el desarrollo se identificaron y resolvieron dos problemas relevantes de calidad de datos: la duplicación de un mismo material en distintos formatos (resuelto mediante una lista blanca de extensiones configurable) y la contaminación con recursos ajenos al contenido académico, como íconos de interfaz (resuelto restringiendo la extracción a un dominio de almacenamiento específico y verificado)."
  ),
  p(
    "La incorporación de una interfaz visual en tiempo real, además de mejorar la experiencia de uso, facilita la detección temprana de errores durante ejecuciones largas con decenas o cientos de archivos."
  ),
  new Paragraph({ text: "", spacing: { after: 200 } }),
];

// ---------- Anexo A: Glosario ----------
const glossarySection = [
  h1("Anexo A. Glosario de términos técnicos"),
  makeTable(
    ["Término", "Definición"],
    [
      ["API REST", "Interfaz de programación que expone recursos mediante peticiones HTTP (GET, POST, etc.) devolviendo datos estructurados, típicamente en formato JSON."],
      ["Token Bearer / JWT", "Credencial de sesión (JSON Web Token) que se envía en la cabecera Authorization de cada petición para demostrar que el usuario está autenticado."],
      ["Endpoint", "Una URL específica de una API que atiende un tipo de petición concreto."],
      ["JSON", "Formato de texto ligero para el intercambio de datos estructurados (JavaScript Object Notation)."],
      ["Regex / Expresión regular", "Patrón de texto usado para buscar o extraer subcadenas que cumplen una estructura determinada."],
      ["S3 (Amazon Simple Storage Service)", "Servicio de almacenamiento de archivos en la nube utilizado por UTP para alojar los materiales descargables."],
      ["TUI (Text User Interface)", "Interfaz de usuario visual construida dentro de una terminal de texto, con paneles, colores y actualización en tiempo real."],
      ["Idempotencia", "Propiedad de una operación que, al repetirse, produce el mismo resultado sin efectos secundarios adicionales (en este caso, no volver a descargar un archivo ya existente)."],
      ["Streaming (descarga por streaming)", "Técnica de transferencia de datos en bloques (chunks) en vez de cargar el archivo completo en memoria antes de guardarlo."],
      ["Sanitizar (nombre de archivo)", "Proceso de limpiar un texto de caracteres no permitidos por el sistema de archivos, para poder usarlo como nombre de carpeta o archivo."],
    ],
    [25, 75]
  ),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- Anexo B: Código fuente completo ----------
const codeSection = [
  h1("Anexo B. Código fuente completo (utp_scraper_v2.py)"),
  p("Se incluye el listado completo del script documentado en este informe, para referencia y trazabilidad."),
  ...codeBlock(scriptLines),
];

// ---------- Ensamblar documento ----------
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT_BODY, size: 22 } },
      heading1: { run: { font: FONT_BODY, size: 30, bold: true, color: COLOR_PRIMARY }, paragraph: { spacing: { before: 400, after: 200 } } },
      heading2: { run: { font: FONT_BODY, size: 26, bold: true, color: COLOR_ACCENT }, paragraph: { spacing: { before: 300, after: 150 } } },
      heading3: { run: { font: FONT_BODY, size: 23, bold: true, color: "404040" }, paragraph: { spacing: { before: 200, after: 100 } } },
    },
  },
  numbering: {
    config: [
      {
        reference: "bullet-list",
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 260 } } } },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          margin: { top: 1418, bottom: 1418, left: 1418, right: 1418 },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              children: [new TextRun({ text: "UTP+class Material Downloader — Informe técnico", size: 16, color: COLOR_MUTED, font: FONT_BODY })],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({ text: "Página ", size: 16, color: COLOR_MUTED, font: FONT_BODY }),
                new TextRun({ children: [PageNumber.CURRENT], size: 16, color: COLOR_MUTED, font: FONT_BODY }),
                new TextRun({ text: " de ", size: 16, color: COLOR_MUTED, font: FONT_BODY }),
                new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: COLOR_MUTED, font: FONT_BODY }),
              ],
            }),
          ],
        }),
      },
      children: [
        ...coverPage,
        ...tocSection,
        ...introSection,
        ...archSection,
        ...flowSection,
        ...dedupSection,
        ...uiSection,
        ...outputSection,
        ...modulesSection,
        ...configSection,
        ...securitySection,
        ...errorsSection,
        ...usageSection,
        ...futureSection,
        ...ethicsSection,
        ...conclusionSection,
        ...glossarySection,
        ...codeSection,
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("./Informe_Tecnico_UTP_Scraper.docx", buffer);
  console.log("Documento generado correctamente.");
});