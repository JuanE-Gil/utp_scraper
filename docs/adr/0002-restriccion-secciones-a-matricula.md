# ADR-0002: Acceso a secciones restringido a la matrícula real del usuario

**Estado:** Cerrada (adoptada, Sprint 2) · **Fecha:** Septiembre 2026

## Contexto
Técnicamente nada impide construir la URL del endpoint con un `sectionId` ajeno a la matrícula; el backend lo podría aceptar. El alcance ético declarado del proyecto (INFORME §15) prohíbe acceder a contenido de otros estudiantes.

## Decisión
**Bloqueo estructural** (historia B4, Won't): la lista de cursos/secciones ofrecida para selección proviene únicamente de la respuesta de matrícula del usuario autenticado, nunca de un identificador ingresado o descubierto manualmente.

## Alternativas
- Permitir ingresar cualquier `sectionId` manualmente (descartada: rompe la premisa ética).

## Consecuencias
- Ningún código futuro accederá a secciones fuera de la matrícula real; el Plan de pruebas B bloquea esto por diseño.
- Esta restricción es vinculante para cualquier agente (ver `AGENTS.md` → Alcance protegido).
