# ADR-0001: No reintentar login con credenciales inválidas

**Estado:** Cerrada (adoptada, Sprint 1) · **Fecha:** Septiembre 2026

## Contexto
Un SSO institucional puede bloquear la cuenta tras intentos fallidos repetidos; reintentar automáticamente con la misma contraseña arriesga el acceso del usuario.

## Decisión
Ante mensaje de credenciales inválidas del SSO, terminar con mensaje explícito y **no reintentar automáticamente**. Nada de memoria de contraseñas ni autofill sobre el mismo prompt.

## Alternativas
- Reintento automático con nuevo prompt (descartada: riesgo de bloqueo de cuenta institucional).

## Consecuencias
- Máquina de estados del login (INFORME §10.1): `ERROR_CREDENCIALES` es terminal.
- El Plan de pruebas A-02 (INFORME §9) fija este comportamiento.
