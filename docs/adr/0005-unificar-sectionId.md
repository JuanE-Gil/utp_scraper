# ADR-0005: `sectionId` como fuente única de verdad del identificador de sección

**Estado:** **Abierta** · **Fecha origen:** Sprint 3 (sept. 2026)

## Contexto
Las dos demos de autenticación buscan el identificador de sección en órdenes distintos (`sectionId → sectionCode → section` vs `section → sectionCode → sectionId`). Arrastrar la ambigüedad al contrato de la v3 garantiza discrepancia entre módulos.

## Decisión propuesta
Unificar el nombre de campo como `sectionId`. **Pendiente:** confirmar contra la respuesta real de la API (campo con el valor que efectivamente se usa en el endpoint `.../sections/{id}/full`).

## Alternativas
- Mantener alias (`sectionCode`, `section`) tal como están las demos (descartada: fuente de contratos inconsistentes).

## Consecuencias
- El contrato de datos del Sprint 3 (INFORME §7) se escribe contra esta única forma.
- **Criterios de cierre:** la captura de la respuesta real de matrícula confirma el campo y su valor admitido como URL.
