# ADR-0006: Framework de GUI aún sin decidir

**Estado:** **Abierta** · **Fecha origen:** Sprint 4 (sept. 2026)

## Contexto
El contrato de eventos (INFORME §4) permite desacoplar la lógica de la presentación, de modo que el framework GUI puede elegirse tarde sin reescribir el motor. Comprometerse a una librería ahora significaría diseñar contra una API sin haber validado el mockup.

## Decisión propuesta
Pendiente entre `PySimpleGUI`/`FreeSimpleGUI` (ligero, MIT) y `PyQt`/`PySide` (potente, más peso). **Criterios de cierre:** mockups §12.2 validados contra los flujos de las Épicas A y B, y confirmación de que el framework permite la pantalla de progreso mínima (§12.2 Pantalla 3).

## Alternativas
- Decidir el framework ya (descartada: mockup sin validar).

## Consecuencias
- Ningún requisito de implementación actual depende de un framework GUI.
- Cuando se cierre, este ADR registra la elección y su evaluación.
