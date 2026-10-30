# AGENTS.md — instrucciones para agentes en este repo

Antes de actuar, leer en este orden:

1. `README.md` — constitución (seguridad y alcance) + mapa documental (un solo dueño por hecho).
2. `INFORME_TECNICO.md` §13 (Kanban) y §16 (próximos pasos) — estado actual del proyecto.
3. `docs/adr/` — si la tarea toca una decisión del Decision Log (§10), el ADR correspondiente manda.

## Reglas duras (obligatorias en toda tarea)

- **Credenciales**: nunca escribir `AUTH_TOKEN`, `USER_ID`, `TENANT_ID` ni IDs reales en código, docs o historial de git. El token equivale a la contraseña mientras esté vigente (~24h). Para pruebas locales: variables de entorno.
- **Documentación**: un solo dueño por hecho. No duplicar contenido entre README, INFORME y ADRs; enlazar.
- **Commits**: Conventional Commits (`feat|fix|docs|refactor|test|chore(scope): ...`); ramas `feature/*` o `develop`, nunca commit directo a `main`.
- **Código**: Python 3.8+, las capas viven en `utp_scraper/` (arquitectura objetivo: INFORME §4). `core` no importa `rich`; la UI consume eventos.
- **No versionar**: `dist/`, `node_modules/`, `.venv/`, `descargas_utp/`, evidencias con datos personales (ver `.gitignore`).
- **Los PDF/DOCX en `dist/` son generados** (regenerables desde el informe); nunca editarlos a mano ni commitearlos.

## Alcance protegido

Solo contenido donde el usuario está matriculado, con su propia sesión. Acceso a secciones de otros estudiantes = fuera de alcance explícito (Épica B4, INFORME §11.2). No implementarlo, no documentarlo.
