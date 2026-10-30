# ADR-0003: Períodos académicos anteriores como opción explícita (B5)

**Estado:** Cerrada (adoptada, Sprint 2) · **Fecha:** Septiembre 2026

## Contexto
La respuesta del endpoint de períodos ya incluye el historial completo (se descarta hoy para conservar solo `CURRENT_PERIOD`). Mostrar siempre todo el historial añadiría fricción al caso de uso principal (descargar el ciclo vigente).

## Decisión
El flujo principal muestra **solo el período vigente**. Ver períodos anteriores es una **historia opcional (B5, prioridad Could)**: una opción explícita repite el flujo B1→B2 con otro `academicPeriodId`.

## Alternativas
- Mostrar siempre todos los períodos (descartada: flujo principal más ruidoso).

## Consecuencias
- **Corregido 2026-10-29:** los ciclos anteriores llegan en la respuesta de `dashboard-courses` (misma llamada que el ciclo vigente); `academicperiods` solo aporta etiquetas legibles y cuál es el vigente. La unión períodos↔cursos se hace por la tupla `(period, acadCareer, module)` — ver `docs/estado_proyecto_fase1.md`.
- Se implementará solo como opción explícita ("Ciclos anteriores" plegado en la GUI, INFORME/plan §6.1), no por defecto.
