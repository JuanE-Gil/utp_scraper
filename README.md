# UTP+class Downloader

Herramienta personal para automatizar el login y la descarga organizada de materiales académicos desde **UTP+class** (plataforma virtual de la UTP) via `api-pao.utpxpedition.com`.

**Estado:** v3 modular: suite **28/28** pytest. Estructura v3 extraída y Fase 1 verificada con sondas reales; faltan `auth` y `ui_gui` (Fases 2–4). Estado de avance: ver `docs/estado_proyecto_fase1.md` y `docs/plan_completo_proyecto_utp.md`.

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
utp_scraper/          → paquete v3 (capas del INFORME §4)
  ├── api.py          → HTTP puro: headers + get_section_full          [✅]
  ├── downloader.py   → sanitize + extract_urls + download_file        [✅ testado]
  ├── core.py         → collect_jobs + run_jobs (contrato de eventos) [✅ testado]
  ├── ui_cli.py       → TUI rich.Live; consume eventos                 [✅]
  ├── main.py         → python -m utp_scraper (credenciales por env)   [✅]
  └── courses.py      → lista de cursos editable (placeholder Épica B)
tests/                → pytest (tests de paridad sobre la lógica del antiguo monolito)
demos/                → demo_utp_auth*.py (login SSO) + tui_mockup.py  [📋 demo, sin integrar]
archive/              → material ajeno al proyecto (app_it.py)
docs/                 → historia/ + adr/  (ver tabla de roles arriba)
index.js + package.json → regeneran dist/ (informes PDF/DOCX): npm run docs
```

Arquitectura objetivo (modular, para GUI): ver `INFORME_TECNICO.md` §4 — faltan las capas `auth`, `ui_gui` y un orquestador completo; llegan con la integración Épica A/B (pendiente).

## Requisitos y uso

```bash
pip install requests rich playwright --break-system-packages
playwright install chromium
```

Uso actual: credenciales por variables de entorno; la lista de cursos es manual (`utp_scraper/courses.py`) hasta integrar la Épica B.

1. Inicia sesión en `class.utp.edu.pe` y abre DevTools (F12) → Network → Fetch/XHR.
2. De una petición a `api-pao.utpxpedition.com` copia `authorization` (sin `Bearer`), `user-id` y `x-tenant-id`.
3. Márcalas como variables de entorno, y completa `courseId`/`sectionId` (URL de "Mis cursos") en `utp_scraper/courses.py`.
4. `python -m utp_scraper`: descarga masiva reorganizada por curso/semana/tema, sin duplicados ni ruido.

Los pasos 1–3 se automatizarán al integrar las Épicas A/B (Fases 2–4, ver docs/plan_completo_proyecto_utp.md).

## 🔒 Seguridad (reglas obligatorias)

- El `AUTH_TOKEN` y la contraseña son los únicos secretos: el token equivale a tu contraseña mientras esté vigente (~24h). **Nunca** los escribas en el código, en docs, ni los subas a un repositorio; usa variables de entorno o campos de la GUI. (Verificado 29-oct-2026, ADR-0007: `user-id` es derivable y `x-tenant-id` es constante pública del front; no son secretos.)
- La contraseña se usa solo en el instante del login: nunca en disco ni en logs.
- Si ya publicaste un valor real en algún sitio: cierra sesión en `class.utp.edu.pe` para invalidar el token.
- Antes de publicar: `grep` de `eyJ`, `TU_TOKEN`, `u2...` en todo el repo **y en el historial git**.

## ⚖️ Alcance y uso responsable

Solo contenido donde el usuario está matriculado, vía su propia sesión, para uso personal (respaldo/estudio offline). El acceso a secciones de otros estudiantes es **fuera de alcance explícito** (historia B4, Won't — ver INFORME §11.2). Revisa el reglamento de la plataforma antes de uso automatizado intensivo.

## 🤝 Contribuciones y licencia

Proyecto personal de código abierto: abre un *issue* con el caso de uso antes de un PR; el backlog del informe (Sección 6) es el punto de partida para priorizar.

Commits: Conventional Commits (`feat|fix|docs|refactor|test|chore(scope): ...`) — ramas `feature/*` sobre `main`, PR o merge directo según tamaño.

Licencia: pendiente (sugerida: MIT). Añade el archivo `LICENSE` antes de publicar como abierto.
