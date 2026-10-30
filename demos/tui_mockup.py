import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(9, 6.4))
ax.set_xlim(0, 100)
ax.set_ylim(0, 70)
ax.axis('off')
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')

LINE_H = 4.6
TOP_PAD = 8.0
BOTTOM_PAD = 2.5

def panel(x, y_top, w, title, color, lines, title_color="#7fd1ff"):
    """Dibuja un panel cuya altura se calcula según la cantidad de líneas,
    y devuelve el y inferior (para encadenar el siguiente elemento)."""
    h = TOP_PAD + len(lines) * LINE_H + BOTTOM_PAD
    y = y_top - h
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2",
                          linewidth=1.6, edgecolor=color, facecolor="#111722")
    ax.add_patch(box)
    ax.text(x + 1.8, y + h - 4.2, title, color=title_color, fontsize=11,
             fontweight='bold', family='monospace')
    ty = y + h - TOP_PAD
    for line, lcolor in lines:
        if line:
            ax.text(x + 1.8, ty, line, color=lcolor, fontsize=9, family='monospace')
        ty -= LINE_H
    return y  # borde inferior del panel

# ---- Header ----
header_h = 7
header_top = 70
header_bottom = header_top - header_h
header = FancyBboxPatch((1, header_bottom), 98, header_h, boxstyle="round,pad=0.3,rounding_size=1",
                         linewidth=1.6, edgecolor="#3fa7ff", facecolor="#0f2436")
ax.add_patch(header)
ax.text(50, header_bottom + header_h / 2 - 1, "UTP+class Material Downloader",
         color="#7fd1ff", fontsize=13, fontweight='bold', ha='center', family='monospace')

gap = 2
row_top = header_bottom - gap

# ---- Panel Estado (izquierda) ----
estado_lines = [
    ("Curso actual:   Estadistica_Inferencial", "#e6e6e6"),
    ("Progreso curso:", "#e6e6e6"),
    ("[############......]  73%  (177/243)", "#7fd1ff"),
    ("Semana/Tema:  Semana_07 - Ejercicio...", "#e6e6e6"),
    ("Archivo:      Semana_7-Video_HCJM.mp4", "#e6e6e6"),
]
estado_bottom = panel(1, row_top, 46, "Estado", "#3f7fff", estado_lines)

# ---- Panel Registro (derecha) ----
registro_lines = [
    ("[OK] Semana_07: Guion_TYBXNA.docx", "#7CE38B"),
    ("[OK] Semana_07: Video_HCJM.mp4", "#7CE38B"),
    ("[--] Semana_07: Democracia.mp4 (ya existe)", "#E3C97C"),
    ("[OK] Semana_07: Identidad_politica_JW.pdf", "#7CE38B"),
    ("[XX] Semana_06: video_corrupto.mp4 - timeout", "#E37C7C"),
]
registro_bottom = panel(49, row_top, 50, "Registro", "#c23b9a", registro_lines)

row_bottom = min(estado_bottom, registro_bottom)

# ---- Footer ----
footer_h = 8
footer_top = row_bottom - gap
footer_bottom = footer_top - footer_h
footer = FancyBboxPatch((1, footer_bottom), 98, footer_h, boxstyle="round,pad=0.3,rounding_size=1",
                         linewidth=1.4, edgecolor="#555555", facecolor="#111722")
ax.add_patch(footer)
fy = footer_bottom + footer_h / 2 - 1
ax.text(13, fy, "Descargados: 142", color="#7CE38B", fontsize=9.5, ha='center', family='monospace')
ax.text(38, fy, "Ya existian: 30", color="#E3C97C", fontsize=9.5, ha='center', family='monospace')
ax.text(63, fy, "Filtrados: 71", color="#9aa0a6", fontsize=9.5, ha='center', family='monospace')
ax.text(87, fy, "Errores: 1", color="#E37C7C", fontsize=9.5, ha='center', family='monospace')

# ---- Nota ----
note_y = footer_bottom - 6
ax.text(50, note_y,
         "Vista simplificada (screen=False): la interfaz se refresca en el mismo lugar de la terminal,\n"
         "sin tomar control de pantalla completa - compatible con terminales embebidas.",
         color="#8b949e", fontsize=8.3, ha='center', family='monospace')

ax.set_ylim(note_y - 6, 70)

plt.tight_layout()
plt.savefig("tui_mockup.png", dpi=170, facecolor=fig.get_facecolor())
print("saved")
