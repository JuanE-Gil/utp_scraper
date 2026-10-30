# ADR-0005: `sectionId` como fuente única de verdad del identificador de sección

**Estado:** Cerrada (adoptada, Fase 1 de v3) · **Fecha origen:** Sprint 3 (sept. 2026) · **Fecha de cierre:** 29 de octubre de 2026

## Contexto
Las dos demos de autenticación buscaban el identificador de sección en órdenes distintos (`sectionId → sectionCode → section` vs `section → sectionCode → sectionId`). Arrastrar la ambigüedad al contrato de la v3 garantizaba discrepancia entre módulos.

## Decisión
Unificar el nombre de campo como `sectionId`, sin alias de respaldo.

## Evidencia (Fase 1)
- La respuesta real de matrícula (`GET /learning/student/{userId}/dashboard-courses`, 31 items) trae `sectionId` en todos los items, único y con forma de UUID (`fase1b_reporte.json`).
- `sectionCode` existe en la misma respuesta pero es otro dato (código de sección, no UUID). Caer en él como alias construiría una URL inválida en `.../sections/{id}/full`.
- El campo `section` no aparece en la respuesta.
- Las llamadas `/full` con el par (`courseId`, `sectionId`) tomado de esa respuesta devolvieron 200 en los 5 ciclos probados.

## Alternativas
- Mantener alias (`sectionCode`, `section`) tal como están las demos (descartada: fuente de contratos inconsistentes y, ahora, comprobadamente incorrecta).

## Consecuencias
- El contrato de datos del Sprint 3 (INFORME §7) se escribe contra esta única forma.
- Un item sin `sectionId` o `courseId` válido se excluye de la lista seleccionable y se avisa en el registro (matriz §8); nunca se sustituye por otro campo (`core._is_valid_course`).
- La identidad de una sección es `sectionId`, no `courseId`: un mismo `courseId` aparece en varias secciones y ciclos.
- **Criterio de cierre cumplido:** captura de la respuesta real de matrícula confirma el campo y su valor admitido como URL.