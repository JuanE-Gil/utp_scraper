# utp_scraper.ui_theme — tokens visuales y ayudantes del rediseño (plan de diseño §5, §8).
# Única fuente de apariencia: fuera de este módulo no se hardcodean colores ni fuentes.
#
# v2 del estilo ("editorial"): barra lateral oscura + panel de contenido blanco, jerarquía por
# tipografía y espacio, bordes de 1 px suaves, iconos de línea y un único acento azul/violeta.
# Regla de fondo: TODO elemento dentro de una zona hereda el fondo de esa zona (por eso BG es
# blanco puro: sin parches de color detrás del texto). Las zonas tintadas pasan su fondo explícito.

import ctypes
import tkinter as tk

import FreeSimpleGUI as sg

from utp_scraper import ui_assets

BRAND = "UTP+class Downloader"
VERSION = "v3.1.0-alpha.1"
STEPS = ("Acceso", "Cursos", "Descarga", "Resumen")

# ─── Superficies ─────────────────────────────────────────────────────────────
BG = "#FFFFFF"            # panel de contenido (fondo base de la ventana)
SURFACE = "#FFFFFF"       # tarjetas, campos
SURFACE_ALT = "#F6F5FC"   # cabeceras de grupo, log, campos de texto, hover
PANEL = "#F3F1FF"         # panel decorativo (ilustración del acceso)
BORDER = "#E8E6F6"        # líneas finas (1 px)
GLOW = "#F4F3FB"          # halo suave exterior de las tarjetas (sombra simulada)
BORDER_IN = "#8D8ABF"     # borde de campos (≈3,2:1 sobre blanco)

# ─── Texto ───────────────────────────────────────────────────────────────────
INK = "#1E1B3A"
INK2 = "#5B5780"
INK3 = "#9C99BE"
WHITE = "#FFFFFF"

# ─── Acentos (azul / violeta) ────────────────────────────────────────────────
BLUE_L = "#DCE4FF"
BLUE = "#4A5FE8"
BLUE_D = "#2F3FB8"
VIOL_L = "#E7DEFF"
VIOL = "#7C4DFF"
VIOL_D = "#5B34C9"
BAR_TRACK = "#E9ECFB"
HOVER = "#3F52D6"
SEL = "#EAEEFF"          # fila de curso seleccionada

# ─── Barra lateral oscura ────────────────────────────────────────────────────
SIDE = "#25233F"
SIDE_HI = "#35325F"       # fila activa
SIDE_LINE = "#37345F"
SIDE_TXT = "#F1F0FF"
SIDE_MUTED = "#A6A3D4"    # ≈6,3:1 sobre SIDE
SIDE_DIM = "#8D8ABF"      # pendiente ≈4,7:1
SIDE_ON = "#B4C3FF"       # acento pastel azul (paso actual)
SIDE_DONE = "#C9B3FF"     # acento pastel violeta (paso completado)

# ─── Estados: (fondo, texto) ─────────────────────────────────────────────────
OK = ("#DDF6EA", "#14693F")
WARN = ("#FFF1D6", "#8A5300")
ERR = ("#FFE1E6", "#B4233F")
INFO = ("#DCE4FF", "#2F3FB8")

# ─── Tipografía (§5.4) ───────────────────────────────────────────────────────
# Si "Segoe UI Semibold" resuelve en tu Windows, puede sustituir al bold: cambiar solo aquí.
FONT = "Segoe UI"
H1 = (FONT, 22, "bold")
SEC = (FONT, 12, "bold")
BODY = (FONT, 10)
BODY_B = (FONT, 10, "bold")
CAP = (FONT, 9)
CAP_B = (FONT, 9, "bold")
LABEL = (FONT, 8, "bold")      # rótulos de sección en mayúsculas
FIG = (FONT, 26, "bold")
MONO = ("Consolas", 9)

_DEEP = {"INPUT": SURFACE_ALT, "TEXT_INPUT": INK, "SCROLL": BORDER, "BORDER": 0,
         "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0}


def dpi_aware():
    """Declarar conciencia de DPI antes de crear la ventana (§10). Fuera de Windows: no-op."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def theme():
    """Registrar y activar el tema UTP+class (paleta §5.1)."""
    sg.theme_add_new("utpplus", {
        "BACKGROUND": BG, "TEXT": INK, **_DEEP,
        "BUTTON": (WHITE, BLUE), "BUTTON1": (WHITE, BLUE),
        "PROGRESS": (BLUE, BAR_TRACK),
    })
    sg.theme("utpplus")


# ─── Imágenes e iconos ───────────────────────────────────────────────────────

def icon(name, bg=None, key=None, p=(0, 0), tip=None):
    """Icono PNG embebido (Lucide). bg = fondo de la zona donde se coloca."""
    return sg.Image(data=ui_assets.get(name), background_color=bg or BG, key=key,
                    pad=p, tooltip=tip)


def ibtn(name, key=None, bg=None, tip=None, p=(0, 0)):
    """Botón de solo icono, plano (p. ej. mostrar/ocultar contraseña)."""
    bg = bg or BG
    return sg.Button("", image_data=ui_assets.get(name), key=key, border_width=0,
                     button_color=(bg, bg), mouseover_colors=(bg, SURFACE_ALT if bg == BG else BORDER),
                     tooltip=tip, pad=p, metadata="I")


def hr(color=None, p=(0, 0)):
    """Línea horizontal de 1 px a todo el ancho de su zona."""
    return sg.Column([[sg.Sizer(0, 1)]], background_color=color or BORDER, pad=p, expand_x=True)


# ─── Texto ───────────────────────────────────────────────────────────────────

def ttl(s, p=(0, 0), bg=None):
    return sg.Text(s, font=H1, text_color=INK, background_color=bg or BG, pad=p)


def sec(s, p=((0, 0), (16, 4)), bg=None):
    return sg.Text(s, font=SEC, text_color=INK, background_color=bg or BG, pad=p)


def label(s, p=(0, 0), bg=None, tc=None):
    """Rótulo de sección en versalitas (mayúsculas con tracking)."""
    return sg.Text(" ".join(s.upper()), font=LABEL, text_color=tc or INK3,
                   background_color=bg or BG, pad=p)


def capt(s, key=None, tc=INK2, font=CAP, p=(0, 0), n=None, just=None, expand_x=False, bg=None):
    kw = {"size": n} if n is not None else {}
    return sg.Text(s, key=key, font=font, text_color=tc, background_color=bg or BG, pad=p,
                   justification=just, expand_x=expand_x, **kw)


def txt(s, key=None, tc=None, font=BODY, expand_x=False, p=(0, 0), n=None, just=None, bg=None):
    kw = {"size": n} if n is not None else {}
    return sg.Text(s, key=key, font=font, text_color=tc or INK, background_color=bg or BG, pad=p,
                   justification=just, expand_x=expand_x, **kw)


def chip(s, estado=None, key=None):
    """Etiqueta tipo "pastilla": fondo suave, texto profundo, relleno interior (polish)."""
    f, t = estado or (BLUE_L, BLUE_D)
    return sg.Text(s, key=key, font=CAP_B, background_color=f, text_color=t, pad=((4, 4), (4, 4)),
                   metadata="CHIP")


def banner(msg, estado=INFO, key=None):
    """Banner de estado a todo el ancho: fondo suave + texto profundo (§8.6)."""
    f, t = estado
    return sg.Column([[sg.Text(msg, font=CAP, text_color=t, background_color=f, pad=(14, 8))]],
                     background_color=f, pad=(0, 8), key=key, expand_x=True)


def card(rows, key=None, p=(0, 6), inner=(20, 16)):
    """Tarjeta: relleno blanco, borde de 1 px y halo suave inferior (sombra simulada: Tk no tiene)."""
    body = sg.Column(rows, background_color=SURFACE, pad=inner, expand_x=True)
    edge = sg.Column([[body]], background_color=SURFACE, pad=(1, 1), expand_x=True)
    ring = sg.Column([[edge]], background_color=BORDER, pad=((3, 3), (2, 5)), expand_x=True)
    return sg.Column([[ring]], background_color=GLOW, pad=p, key=key, expand_x=True)


# ─── Botones ─────────────────────────────────────────────────────────────────

def btnP(label, key=None, dis=False, expand_x=False, brk=False):
    """Botón principal; brk=True hace que Enter dispare este botón (§8.1)."""
    return sg.Button(label, key=key, button_color=(WHITE, BLUE), mouseover_colors=(WHITE, HOVER),
                     disabled_button_color=(INK3, BORDER), disabled=dis, border_width=0,
                     bind_return_key=brk, font=BODY_B, pad=((0, 0), (6, 6)),
                     expand_x=expand_x, metadata="P")


def btnS(label, key=None, dis=False):
    """Botón secundario: contorno de 1 px azul sobre blanco (el contorno lo da polish)."""
    return sg.Button(label, key=key, button_color=(BLUE, SURFACE), mouseover_colors=(BLUE, BLUE_L),
                     disabled_button_color=(INK3, BORDER), disabled=dis, border_width=0,
                     font=BODY_B, pad=((8, 8), (2, 2)), metadata="S")


def btnT(label, key=None, dis=False, bgc=BG, p=(4, 4), visible=True, fg=BLUE, hover=None):
    """Botón de texto (enlace). bgc = fondo de la zona; hover = (texto, fondo) al pasar el ratón."""
    hov = hover or (fg, SURFACE_ALT if bgc == BG else BORDER)
    return sg.Button(label, key=key, button_color=(fg, bgc), mouseover_colors=hov,
                     disabled_button_color=(INK3, bgc), disabled=dis, visible=visible,
                     border_width=0, font=CAP_B, pad=p, metadata="T")


def inp(key, size=(26, 1), font=BODY, pad=(0, 4), password=False, expand_x=False, enable_events=False,
        default=""):
    """Campo de texto: relleno gris muy suave, sin borde nativo (el borde fino lo pone polish)."""
    kw = {"password_char": "•"} if password else {}
    return sg.Input(default, key=key, size=size, font=font, pad=pad, background_color=SURFACE_ALT,
                    text_color=INK, border_width=0, expand_x=expand_x, enable_events=enable_events,
                    metadata="INPUT", **kw)


def search_field(key):
    """Búsqueda: un solo campo con lupa integrada y contorno de 1 px (Input con eventos)."""
    field = sg.Input("", key=key, size=(30, 1), font=(FONT, 11), background_color=SURFACE_ALT,
                     text_color=INK, border_width=0, pad=(0, 0), expand_x=True,
                     enable_events=True, metadata="INPUT0")
    inner = sg.Column([[icon("search", bg=SURFACE_ALT, p=((14, 4), (0, 0))), field]],
                      background_color=SURFACE_ALT, pad=(1, 1), expand_x=True)
    return sg.Column([[inner]], background_color=BORDER, pad=(0, 0), expand_x=True)


def toggle_log(prefix):
    return btnT("Detalle", key=f"{prefix}LOGT")


def status_word(ev):
    """(palabra, estado) por evento terminal — nunca solo color (§4.3)."""
    return {"downloaded": ("Descargado", OK),
            "skipped_existing": ("Ya existía", WARN),
            "filtered_format": ("Filtrado", INFO),
            "error": ("Error", ERR)}[ev]


# ─── Pulido de widgets Tk (lo que FreeSimpleGUI no expone) ───────────────────

def _cfg(widget, **kw):
    try:
        widget.configure(**kw)
    except tk.TclError:
        pass


def polish(w):
    """Ajustes finos sobre los widgets Tk ya construidos (idempotente; solo apariencia):
    relleno interior de botones y chips, contorno del botón secundario, anillo de foco de los
    campos, cursor de mano. Se invoca tras construir cada vista."""
    for el in w.element_list():
        role = getattr(el, "metadata", None)
        wd = getattr(el, "widget", None)
        if wd is None or role is None:
            continue
        if role == "P":
            _cfg(wd, padx=26, pady=7, cursor="hand2", relief="flat", highlightthickness=0)
        elif role == "S":
            _cfg(wd, padx=16, pady=5, cursor="hand2", relief="flat",
                 highlightthickness=1, highlightbackground=BLUE, highlightcolor=BLUE)
        elif role == "T":
            _cfg(wd, padx=8, pady=3, cursor="hand2", relief="flat", highlightthickness=0)
        elif role == "I":
            _cfg(wd, padx=4, pady=4, cursor="hand2", relief="flat", highlightthickness=0)
        elif role == "CHIP":
            _cfg(wd, padx=9, pady=3)
        elif role == "MSG":
            _cfg(wd, padx=14, pady=8, anchor="w", justify="left")
        elif role == "INPUT0":
            _cfg(wd, relief="flat", borderwidth=8, highlightthickness=0, insertbackground=INK)
        elif role == "LOG":
            _cfg(wd, relief="flat", borderwidth=0, highlightthickness=1, highlightbackground=BORDER,
                 padx=14, pady=10)
        elif role == "INPUT":
            _cfg(wd, relief="flat", borderwidth=7, highlightthickness=1,
                 highlightbackground=BORDER_IN, highlightcolor=BLUE, insertbackground=INK)


def set_msg(el, text, estado=None):
    """Mensaje reservado del formulario: sin estado = texto discreto; con estado = banner coloreado."""
    f, t = estado if estado else (BG, INK2)
    el.update(text, background_color=f, text_color=t)


def paint_tree(widget, bg, keep=(BORDER,)):
    """Pinta `widget` y sus descendientes con `bg`, salvo las líneas finas (color en `keep`)."""
    try:
        if str(widget.cget("background")).upper() in keep:
            return
    except tk.TclError:
        pass
    _cfg(widget, background=bg)
    _cfg(widget, activebackground=bg)
    for ch in widget.winfo_children():
        paint_tree(ch, bg, keep)
