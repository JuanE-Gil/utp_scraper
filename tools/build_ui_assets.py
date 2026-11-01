# tools/build_ui_assets.py — genera utp_scraper/ui_assets.py (PNG embebidos en base64).
# Se ejecuta SOLO cuando cambian los recursos; la aplicación no necesita resvg_py.
#
#   pip install resvg-py      (rasterizador SVG→PNG en puro wheel; cairosvg falla en
#                              Windows: cairocffi no encuentra libcairo-2.dll sin GTK)
#   npm pack lucide-static && tar xzf lucide-static-*.tgz        (iconos, licencia ISC)
#   python tools/build_ui_assets.py package/icons utp_scraper/ui_assets.py [carpeta_previews]
#
# Iconos: Lucide (ISC) — Copyright (c) Lucide Icons and Contributors; portions (c) Cole Bemis 2013-2022
# (Feather, MIT). El aviso se conserva en la cabecera del módulo generado.
# Marca, insignias e ilustración: originales de este proyecto.

import base64
import os
import re
import sys

import resvg_py

ICON_DIR = sys.argv[1] if len(sys.argv) > 1 else "package/icons"
OUT = sys.argv[2] if len(sys.argv) > 2 else "utp_scraper/ui_assets.py"
PREVIEW = sys.argv[3] if len(sys.argv) > 3 else None

STROKE = "1.8"

# clave: (icono lucide, color, tamaño px)
ICONS = {
    # barra lateral (20 px): pendiente / activo / completado
    "nav_key_dim": ("key-round", "#8D8ABF", 20), "nav_key_on": ("key-round", "#B4C3FF", 20),
    "nav_book_dim": ("book-open", "#8D8ABF", 20), "nav_book_on": ("book-open", "#B4C3FF", 20),
    "nav_dl_dim": ("download", "#8D8ABF", 20), "nav_dl_on": ("download", "#B4C3FF", 20),
    "nav_ok_dim": ("circle-check", "#8D8ABF", 20), "nav_ok_on": ("circle-check", "#B4C3FF", 20),
    "nav_done": ("circle-check", "#C9B3FF", 20),
    "side_logout": ("log-out", "#A6A3D4", 16),
    "side_user": ("user-round", "#A6A3D4", 16),
    # contenido
    "search": ("search", "#8D8ABF", 16),
    "refresh": ("refresh-cw", "#4A5FE8", 15),
    "folder": ("folder", "#4A5FE8", 16),
    "folder_open_w": ("folder-open", "#FFFFFF", 16),
    "eye": ("eye", "#5B5780", 18), "eye_off": ("eye-off", "#5B5780", 18),
    "lock": ("lock", "#8D8ABF", 14),
    "alert": ("circle-alert", "#B4233F", 16),
    "warn": ("triangle-alert", "#8A5300", 16),
    "info": ("info", "#2F3FB8", 16),
    "check_w": ("check", "#FFFFFF", 14),
}


def lucide(name, color, size):
    svg = open(os.path.join(ICON_DIR, name + ".svg"), encoding="utf-8").read()
    svg = svg.replace("currentColor", color)
    svg = re.sub(r'stroke-width="[^"]*"', f'stroke-width="{STROKE}"', svg, count=1)
    return svg2png(svg, size, size)


MARK = """<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 40 40">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#5B72F5"/><stop offset="1" stop-color="#9468FF"/></linearGradient></defs>
<rect width="40" height="40" rx="11" fill="url(#g)"/>
<path d="M20 9.5v15M13.5 18.5l6.5 6.5 6.5-6.5M11 30h18" fill="none" stroke="#fff" stroke-width="2.7"
 stroke-linecap="round" stroke-linejoin="round"/></svg>"""


def svg2png(svg, w=None, h=None):
    """Rasteriza con resvg_py; el tamaño explícito evita que el PNG dependa
    del width/height intrínseco del SVG (MARK lo redefine por formato)."""
    kw = {}
    if w:
        kw["width"] = w
    if h:
        kw["height"] = h
    out = resvg_py.svg_to_bytes(svg_string=svg, **kw)
    return bytes(out) if not isinstance(out, bytes) else out


def badge(bg, fg, glyph):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 56 56">
<circle cx="28" cy="28" r="28" fill="{bg}"/>
<g transform="translate(28 28) scale(1.5) translate(-12 -12)" fill="none" stroke="{fg}" stroke-width="1.8"
 stroke-linecap="round" stroke-linejoin="round">{glyph}</g></svg>"""


CHECK = '<path d="M5 12.5l4.5 4.5L19 7.5"/>'
ALERT = '<path d="M12 3.5 2.5 20h19z"/><path d="M12 9.5v5M12 17.4v.1"/>'

# Ilustración original (trazo fino, azules y violetas pastel): montañas, nubes, sol y una "tarjeta de
# descarga" flotante. 288 x 260.
ART = """<svg xmlns="http://www.w3.org/2000/svg" width="288" height="260" viewBox="0 0 288 260"
 fill="none" stroke-linecap="round" stroke-linejoin="round">
<circle cx="226" cy="56" r="24" fill="#F3EEFF" stroke="#BBA6FF" stroke-width="1.6"/>
<path d="M36 82h44a13 13 0 0 0-2-25.8 19 19 0 0 0-36 5.5A10.5 10.5 0 0 0 36 82z" fill="#FFFFFF" stroke="#C6C3EA" stroke-width="1.6"/>
<path d="M214 118h38a10 10 0 0 0-1.5-19.8 15 15 0 0 0-28.5 4.4A8 8 0 0 0 214 118z" fill="#FFFFFF" stroke="#D2CFEF" stroke-width="1.4"/>
<path d="M-6 198 54 126l30 38 44-64 62 92 28-30 76 62V270H-6z" fill="#EEEBFD" stroke="#C6C3EA" stroke-width="1.6"/>
<path d="M-6 230l68-52 40 34 52-44 66 62 30-24 44 34V270H-6z" fill="#E3E8FF" stroke="#B3BFF3" stroke-width="1.6"/>
<g stroke="#9DB0F2" stroke-width="1.5" fill="#F4F6FF">
<path d="M30 232l11-24 11 24z"/><path d="M41 232v8"/><path d="M52 236l8-18 8 18z"/><path d="M60 236v7"/>
<path d="M236 238l9-20 9 20z"/><path d="M245 238v7"/></g>
<g transform="translate(94 52)">
<rect x="8" y="10" width="92" height="116" rx="12" fill="#EDE9FF" stroke="#C6C3EA" stroke-width="1.5"/>
<rect x="0" y="0" width="92" height="116" rx="12" fill="#FFFFFF" stroke="#B9B6E3" stroke-width="1.7"/>
<path d="M16 22h34M16 34h58M16 46h46" stroke="#D2CFEF" stroke-width="3"/>
<circle cx="46" cy="86" r="21" fill="#EEF1FF" stroke="#8FA4F7" stroke-width="1.7"/>
<path d="M46 76v18M38 87l8 8 8-8" stroke="#5B72F5" stroke-width="2.6"/>
</g></svg>"""


CHK_OFF = """<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">
<rect x="1.5" y="1.5" width="17" height="17" rx="5" fill="#FFFFFF" stroke="#8D8ABF" stroke-width="1.6"/></svg>"""
CHK_ON = """<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">
<rect x="0.5" y="0.5" width="19" height="19" rx="5.5" fill="#4A5FE8"/>
<path d="M5.4 10.3l3.1 3.1 6.1-6.6" fill="none" stroke="#fff" stroke-width="2.2"
 stroke-linecap="round" stroke-linejoin="round"/></svg>"""


def b64(png: bytes) -> str:
    return base64.b64encode(png).decode("ascii")


def main():
    assets = {k: b64(lucide(n, c, s)) for k, (n, c, s) in ICONS.items()}
    previews = {k: lucide(n, c, s) for k, (n, c, s) in ICONS.items()}
    mark32 = svg2png(MARK.format(s=32), 32, 32)
    mark40 = svg2png(MARK.format(s=40), 40, 40)
    badge_ok = svg2png(badge("#E7DEFF", "#7C4DFF", CHECK), 56, 56)
    badge_warn = svg2png(badge("#FFF1D6", "#8A5300", ALERT), 56, 56)
    art = svg2png(ART, 288, 260)
    chk_off = svg2png(CHK_OFF, 20, 20)
    chk_on = svg2png(CHK_ON, 20, 20)
    assets.update(chk_off=b64(chk_off), chk_on=b64(chk_on))
    previews.update(chk_off=chk_off, chk_on=chk_on)
    assets.update(mark32=b64(mark32), mark40=b64(mark40), badge_ok=b64(badge_ok),
                  badge_warn=b64(badge_warn), art=b64(art))
    previews.update(mark32=mark32, mark40=mark40, badge_ok=badge_ok, badge_warn=badge_warn, art=art)

    lines = [
        "# utp_scraper.ui_assets — recursos gráficos embebidos (PNG en base64). GENERADO: no editar a mano.",
        "# Regenerar con tools/build_ui_assets.py. La app no necesita resvg_py para usarlos.",
        "#",
        "# Iconos de línea: Lucide (https://lucide.dev), licencia ISC.",
        "#   Copyright (c) Lucide Icons and Contributors. Portions (c) Cole Bemis 2013-2022 (Feather, MIT).",
        "#   Permission to use, copy, modify, and/or distribute this software for any purpose with or without",
        "#   fee is hereby granted, provided that the above copyright notice and this permission notice appear",
        "#   in all copies. THE SOFTWARE IS PROVIDED \"AS IS\" WITHOUT WARRANTY OF ANY KIND.",
        "# Marca, insignias e ilustración: originales de este proyecto.",
        "",
        "A = {",
    ]
    for k in sorted(assets):
        v = assets[k]
        lines.append(f'    "{k}": (')
        for i in range(0, len(v), 96):
            lines.append(f'        "{v[i:i + 96]}"')
        lines.append("    ),")
    lines += ["}", "", "", "def get(name: str) -> str:", '    """PNG en base64 listo para sg.Image(data=...) / Button(image_data=...)."""',
              "    return A[name]", ""]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"{len(assets)} recursos -> {OUT} ({os.path.getsize(OUT) // 1024} KB)")
    if PREVIEW:
        os.makedirs(PREVIEW, exist_ok=True)
        for k, png in previews.items():
            open(os.path.join(PREVIEW, k + ".png"), "wb").write(png)


if __name__ == "__main__":
    main()