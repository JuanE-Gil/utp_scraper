# ADR-0006: Framework de GUI aún sin decidir

**Estado:** **Abierta** · **Fecha origen:** Sprint 4 (sept. 2026)

## Contexto
El contrato de eventos (INFORME §4) permite desacoplar la lógica de la presentación, de modo que el framework GUI puede elegirse tarde sin reescribir el motor. Comprometerse a una librería ahora significaría diseñar contra una API sin haber validado el mockup.

## Decisión propuesta
Pendiente entre `PySimpleGUI`/`FreeSimpleGUI` (ligero) y `PyQt`/`PySide` (potente, más peso). **Licencia verificada 30-oct-2026:** los metadatos del paquete FreeSimpleGUI 5.1.0 declaran **LGPLv3+** (no MIT, como figuraba antes de esta enmienda). La LGPL permite usarla desde una aplicación propia incluso si esta es cerrada; al empaquetar con PyInstaller conviene un formato que permita sustituir la biblioteca y conservar el aviso de licencia. No somos abogados: confirmar obligaciones de LGPL antes de distribuir a terceros. Evitar PyQt6 (GPL/comercial); PySide6, si algún día llega el nivel C, es LGPLv3 igual que Python. Regla de Python del repo: PySide6 exigiría 3.9+ (venv real: 3.11) — pendiente de enmendar la regla si se adopta Qt. **Criterios de cierre:** mockups §12.2 validados contra los flujos de las Épicas A y B, y confirmación de que el framework permite la pantalla de progreso mínima (§12.2 Pantalla 3).

## Alternativas
- Decidir el framework ya (descartada: mockup sin validar).

## Consecuencias
- Ningún requisito de implementación actual depende de un framework GUI.
- Cuando se cierre, este ADR registra la elección y su evaluación.
