# ADR-0007: Login institucional por password grant (ROPC), sin navegador

**Fecha:** 29 de octubre de 2026
**Estado:** Cerrada (adoptada; evidencia directa contra producción

## Contexto

El plan (Épica A, INFORME §10) contemplaba Playwright para el login SSO:
Microsoft/Azure AD en pantalla, popup `#idSIButton9`, capturar headers del
dashboard. Costo: Chromium en el ejecutable (~150–300 MB), login lento,
fragilidad ante cambios del markup de Microsoft (riesgo señalizado por la
sesión dev-team del mismo día).

El JWT de la API se emite en Keycloak (`sso.utp.edu.pe`, realm `Xpedition`,
client `pao-web`, el cliente del propio front-end web).

## Decisión

Login por **Resource Owner Password Credentials** contra el token endpoint de
Keycloak, verificado con `tools/probe_ropc_api.py`:

```text
POST https://sso.utp.edu.pe/auth/realms/Xpedition/protocol/openid-connect/token
grant_type=password · client_id=pao-web · scope=openid roles-client-pao-web
profile email roles-realm-xpedition · username · password
```

Resultado en producción: `access_token` (24 h) + `refresh_token`
(`refresh_expires_in` 90 000 s ≈ 25 h). Headers de la API llamadas subsecuentes:

- `authorization: Bearer <access_token>` — **el prefijo Bearer es obligatorio**;
  sin él, el gateway (403 `explicit deny in an identity-based policy`),
  con o sin las demás cabeceras correctas.
- `user-id`, `x-tenant-id`, `user-role: STUDENT` (los de la sesión, capturados
  de DevTools una vez; ver `docs/estado_proyecto_fase1.md`).

Verificado end-to-end: `GET /learning/student/{userId}/dashboard-courses`
→ 200, 31 cursos, con el token del ROPC y `requests` puro.

## Consecuencias

- **Playwright se elimina** de Fase 3 (y del ejecutable): la Fase 3 queda
  reducida a `utp_scraper/auth.py` ≈ una función `login() -> (access,
  refresh)` más `refresh()`.
- La sesión >24 h se renueva por el refresh token (~1 llamada), sin re-login.
- `user-id`/`x-tenant-id` no son derivables del token (el `sub` del JWT NO
  sirve de `user-id`); deben pedirse al usuario una vez (o se obtienen luego
  si aparece un endpoint de perfil que los devuelva — diferido).
- Riesgo aceptado: el direct grant (`pao-web`) está habilitado hoy pero es una
  decisión del proveedor; si lo desactivan, la sonda lo detecta
  (`unauthorized_client`) y se revisita la decisión.
- La contraseña viaja en el cuerpo del POST con TLS, idéntico a ROPC estándar;
  nunca en disco (regla del repo).
