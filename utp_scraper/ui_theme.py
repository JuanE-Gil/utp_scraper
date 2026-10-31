# utp_scraper.ui_theme — tokens visuales y ayudantes del rediseño (plan de diseño §5, §8).
# Única fuente de apariencia: fuera de este módulo no se hardcodean colores ni fuentes.

import ctypes

import FreeSimpleGUI as sg

BRAND = "UTP+class Downloader"
VERSION = "v3.1.0-alpha.1"
STEPS = ("Acceso", "Cursos", "Descarga", "Resumen")

# §5.1 Paleta (tema claro)
BG = "#F5F4FF"            # bg-app
SURFACE = "#FFFFFF"       # surface
SURFACE_ALT = "#EEF0FF"   # surface-alt
BORDER = "#DAD8F5"        # border-soft
BORDER_IN = "#8D8ABF"     # border-input

INK = "#1E1B3A"           # text-primary
INK2 = "#5B5780"          # text-secondary
INK3 = "#9C99BE"          # text-disabled
WHITE = "#FFFFFF"         # text-on-accent

BLUE_L = "#DCE4FF"        # accent-blue-100
BLUE = "#4A5FE8"          # accent-blue-600
BLUE_D = "#2F3FB8"        # accent-blue-700
VIOL_L = "#E7DEFF"        # accent-violet-100
VIOL = "#7C4DFF"          # accent-violet-600
VIOL_D = "#5B34C9"        # accent-violet-700
BAR_TRACK = "#E3E6FA"     # pista de barra de progreso
HOVER = "#3F52D6"         # hover del botón principal (§5.1)

# §5.1 Estados: (fondo, texto)
OK = ("#DDF6EA", "#14693F")
WARN = ("#FFF1D6", "#8A5300")
ERR = ("#FFE1E6", "#B4233F")
INFO = ("#DCE4FF", "#2F3FB8")

# §5.4 Tipografía.
# shortcut: "Segoe UI Semibold" no verificado en todas las máquinas (plan §5.4); usar Segoe UI bold
# plan B del propio diseño. Si el usuario la confirma y prefiere Semibold, cambiar solo aquí.
H1 = ("Segoe UI", 18, "bold")
SEC = ("Segoe UI", 12, "bold")
BODY = ("Segoe UI", 10)
CAP = ("Segoe UI", 9)
FIG = ("Segoe UI", 22, "bold")
MONO = ("Consolas", 9)

_DEEP = {  # theme_add_new exige tabla completa; estas claves neutras completan la nuestra
    "INPUT": SURFACE, "TEXT_INPUT": INK, "SCROLL": SURFACE_ALT, "BORDER": 1,
    "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0,
}


def dpi_aware():
    """Declarar conciencia de DPI antes de crear la ventana (§10). Fuera de Windows: no-op."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def theme():
    """Registrar y activar el tema UTP+class (paleta §5.1)."""
    sg.theme_add_new("utpplus", {
        "BACKGROUND": BG, "TEXT": INK, **{k: v for k, v in _DEEP.items()},
        "BUTTON": (WHITE, BLUE), "BUTTON1": (WHITE, BLUE),
        "PROGRESS": (BLUE, BAR_TRACK),
    })
    sg.theme("utpplus")


# Ayudantes:Reducen la repetición de pad/colores en cada vista.

def ttl(s, p=(0, 0)):
    return sg.Text(s, font=H1, text_color=INK, pad=p)


def sec(s, p=((0, 0), (16, 4))):
    return sg.Text(s, font=SEC, text_color=INK, pad=p)


def capt(s, key=None, tc=INK2, font=CAP, p=(0, 0), n=None, just=None, expand_x=False):
    kw = {"size": n} if n is not None else {}
    return sg.Text(s, key=key, font=font, text_color=tc, pad=p,
                   justification=just, expand_x=expand_x, **kw)


def txt(s, key=None, tc=None, font=BODY, expand_x=False, p=(0, 0), n=None, just=None):
    kw = {"size": n} if n is not None else {}
    return sg.Text(s, key=key, font=font, text_color=tc or INK, pad=p,
                   justification=just, expand_x=expand_x, **kw)


def chip(s, estado=None, key=None):
    f, t = estado or (BLUE_L, BLUE_D)
    return sg.Text(s, key=key, font=("Segoe UI", 9, "bold"), background_color=f,
                   text_color=t, pad=((8, 8), (4, 4)))


def banner(msg, estado=INFO, key=None):
    """Banner de estado a todo el ancho: fondo suave + texto profundo (§8.6)."""
    f, t = estado
    return sg.Column([[sg.Text(msg, font=CAP, text_color=t, background_color=f,
                               pad=(12, 6))]], background_color=f, pad=(0, 8),
                     key=key, expand_x=True)


def card(rows, key=None, p=(1, 1)):
    """Tarjeta: exterior 1 px border-soft, interior blanco (§5.6: sin esquinas nativas)."""
    inner = [sg.Column(rows, background_color=SURFACE, pad=(16, 12))]
    return sg.Column([inner], background_color=BORDER, pad=p, key=key)


def btnP(label, key=None, dis=False, expand_x=False, brk=False):
    """Botón principal; brk=True hace que Enter dispare este botón (§8.1)."""
    return sg.Button(label, key=key, button_color=(WHITE, BLUE), mouseover_colors=(WHITE, HOVER),
                     disabled_button_color=(INK3, BORDER), disabled=dis,
                     bind_return_key=brk,
                     font=("Segoe UI", 10, "bold"), pad=((16, 16), (6, 6)), expand_x=expand_x)


def btnS(label, key=None, dis=False):
    return sg.Button(label, key=key, button_color=(BLUE, SURFACE), mouseover_colors=(BLUE, BLUE_L),
                     disabled_button_color=(INK3, BORDER), disabled=dis,
                     font=("Segoe UI", 10, "bold"), pad=((16, 16), (2, 2)))


def btnT(label, key=None, dis=False, bgc=BG, p=(4, 4), visible=True):
    """Botón de texto (enlace)."""
    return sg.Button(" " + label, key=key, button_color=(BLUE, bgc),
                     mouseover_colors=(BLUE, BLUE_L), disabled_button_color=(INK3, bgc),
                     disabled=dis, visible=visible, font=("Segoe UI", 9, "bold"), pad=p)


def toggle_log(prefix):
    return btnT("Detalle", k=f"{prefix}LOGT")


def status_word(ev):
    """(palabra, estado) por evento terminal — nunca solo color (§4.3)."""
    return {"downloaded": ("Descargado", OK),
            "skipped_existing": ("Ya existía", WARN),
            "filtered_format": ("Filtrado", INFO),
            "error": ("Error", ERR)}[ev]
