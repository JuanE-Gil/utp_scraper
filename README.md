# UTP+class Downloader

Herramienta personal para automatizar el login y la descarga organizada de materiales académicos desde **UTP+class** (plataforma virtual de la UTP) via `api-pao.utpxpedition.com`.

**Estado:** v3 en fase de documentación y especificación (Scrum simplificado). El motor de descarga (`utp_scraper_v2.2.py`) funciona; la integración login → selección de cursos → descarga está especificada pero sin implementar. Estado de avance: ver `INFORME_TECNICO.md` (Kanban §13 y Próximos pasos §16).

---

## Documentación (roles de cada fuente)

| Fuente | Rol | Para qué se consulta |
|---|---|---|
| `README.md` (este) | **Constitución + Mapa** | Reglas obligatorias (seguridad, alcance), dónde está cada cosa y requisitos de uso. |
| `INFORME_TECNICO.md` | **Status + History** | Única fuente canónica de: estado de avance, backlog, sprints, matriz de errores, plan de pruebas, Decision Log (§10) y mockups. |
| `docs/historia/resumen-auth-demo.md` | **History** (congelado, saneado) | Evidencia de origen de la demo de autenticación (ingeniería inversa del SSO). No actualizar; el informe vigente la reemplaza. |
| `dist/` | Artefactos generados (PDF/DOCX) | Regenerables desde el informe; **no se versionan**. |

Regla de oro: **un solo dueño por hecho**. Donde ya existe un hecho, enlázalo; no lo copies a otro documento.

## Estructura del código

```
utp_scraper_v2.2.py   → motor de descarga v2.2 (monolítico, funcional)   [✅ implementado]
demo_utp_auth*.py     → demos de login SSO + obtención de cursos         [✅ demo, sin integrar]
app_it.py             → variante de trabajo del scraper                  [✅ implementado]
tui_mockup.py         → mockup interactivo de la futura selección TUI    [📋 diseño]
```

Arquitectura objetivo (modular, para GUI): ver `INFORME_TECNICO.md` §4 — separación `auth / api / downloader / core / ui_cli / ui_gui / main` con contrato de eventos entre `core` y la presentación.

## Requisitos y uso

```bash
pip install requests rich playwright --break-system-packages
playwright install chromium
```

Uso actual (manual hasta completar la integración):

1. Inicia sesión en `class.utp.edu.pe` y abre DevTools (F12) → Network → Fetch/XHR.
2. De una petición a `api-pao.utpxpedition.com` copia `authorization` (sin `Bearer`), `user-id` y `x-tenant-id`.
3. De "Mis cursos", copia `courseId` y `sectionId` de la URL de cada curso y complétalos en la sección `CONFIGURA ESTO` de `utp_scraper_v2.2.py`.
4. Ejecuta el script: descarga masiva reorganizada por curso/semana/tema, sin duplicados ni ruido.

Los pasos 1–3 se automatizarán al integrar las Épicas A/B del informe.

## 🔒 Seguridad (reglas obligatorias)

- El `AUTH_TOKEN` equivale a tu contraseña mientras esté vigente (~24h). **Nunca** lo escribas en el código, en docs, ni lo subas a un repositorio; usa variables de entorno o `config_local.py` (gitignored).
- La contraseña se usa solo en el instante del login: nunca en disco ni en logs.
- Si ya publicaste un valor real en algún sitio: cierra sesión en `class.utp.edu.pe` para invalidar el token.
- Antes de publicar: `grep` de `eyJ`, `TU_TOKEN`, `u2...` en todo el repo **y en el historial git**.

## ⚖️ Alcance y uso responsable

Solo contenido donde el usuario está matriculado, vía su propia sesión, para uso personal (respaldo/estudio offline). El acceso a secciones de otros estudiantes es **fuera de alcance explícito** (historia B4, Won't — ver INFORME §11.2). Revisa el reglamento de la plataforma antes de uso automatizado intensivo.

## 🤝 Contribuciones y licencia

Proyecto personal de código abierto: abre un *issue* con el caso de uso antes de un PR; el backlog del informe (Sección 6) es el punto de partida para priorizar.

Commits: Conventional Commits (`feat|fix|docs|refactor|test|chore(scope): ...`) — ramas `feature/*` sobre `main`, PR o merge directo según tamaño.

Licencia: pendiente (sugerida: MIT). Añade el archivo `LICENSE` antes de publicar como abierto.
