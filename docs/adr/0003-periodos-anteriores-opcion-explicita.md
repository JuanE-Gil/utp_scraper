# ADR-0003: Períodos académicos anteriores como opción explícita (B5)

**Estado:** Cerrada (adoptada, Sprint 2) · **Fecha:** Septiembre 2026

## Contexto
La respuesta del endpoint de períodos ya incluye el historial completo (se descarta hoy para conservar solo `CURRENT_PERIOD`). Mostrar siempre todo el historial añadiría fricción al caso de uso principal (descargar el ciclo vigente).

## Decisión
El flujo principal muestra **solo el período vigente**. Ver períodos anteriores es una **historia opcional (B5, prioridad Could)**: una opción explícita repite el flujo B1→B2 con otro `academicPeriodId`.

## Alternativas
- Mostrar siempre todos los períodos (descartada: flujo principal más ruidoso).

## Consecuencias
- El historial de `academicPeriods` queda disponible sin trabajo adicional extra (§11.3); se implementará solo como opción explícita, no por defecto.
