# ADR-0004: Mecanismo de selección de cursos — checklist interactivo vs prompt de texto

**Estado:** **Abierta** · **Fecha origen:** Sprint 2 (sept. 2026)

## Contexto
El prompt de texto (`"1"`, `"1,3"`, `"todos"`) no requiere dependencias nuevas (`rich.prompt`); un checklist interactivo (`questionary`/`InquirerPy`) es más intuitivo. Ya existió un problema similar de compatibilidad con `rich screen=True` en IDEs, por lo que el comportamiento en terminales embebidas debe validarse antes de adoptarlo.

## Decisión propuesta
Evaluar el checklist interactivo explícitamente en terminales embebidas antes de adoptarlo; mientras eso no se demuestre, el prompt de texto es el mecanismo vigente (mockup textual en INFORME §12.1).

## Alternativas
- Checklist interactivo (`questionary`, `InquirerPy`) — ventaja: más intuitivo; riesgo: terminales embebidas.
- Menú simple (`simple-term-menu`) — descartada: sin selección múltiple nativa.

## Consecuencias
- Bloquea la implementación de B2 hasta validar checklist en terminal embebida.
- **Criterios de cierre:** una prueba en VS Code/JetBrains (IDE típico del usuario) que muestre flechas+espacio funcionales sin degradar la TUI.
