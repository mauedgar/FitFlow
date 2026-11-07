---
document_id: FF-ISSUE43-POST-SIGNUP-COMPOSITION-20261107-001
status: CANDIDATE_NOT_ACCEPTED
authority: issue43
baseline: 1ae33b225ed7de2a89116a97c97cf30b339fa0ce
sot_blob: f36307af0777fd3b493792ad42115fec56ac44b3
---

# FitFlow #43 — composición aislada sobre onboarding #99

## Estado y decisiones

Candidato independiente desde el merge exacto PR99. Fuente de la decisión de nuevas contraseñas: [ruling Issue43](https://github.com/mauedgar/FitFlow/issues/43#issuecomment-6582023324). La rama histórica PR51 `b77d21c91a353a3dea90c61979954f0edefe6b02`, tree `54e0f137e083596f2ed690159361c6ea0625f18b`, conserva IR002 **0F/1A** y no es integrable sin adaptación; no se marca superseded ni cerrada por este candidato.

## Alcance y origen de cambios

1. `backend/app/core/security.py`: portar solo las funciones nativas bcrypt y el límite de nuevas contraseñas de #51. **Conservar íntegra** la sección JWT del develop actual; no volver a código antiguo de refresh/logout.
2. `backend/app/schemas/user.py`: mantener `PublicUserRegistration` (rol externo prohibido) y `PublicClientRegistration` (nombre/apellido separados) aceptados en #95/#99; validar password en **ambos** y en `UserCreate/UserUpdate`. Se evita un 500 por `get_password_hash` previo al bloque rollback del servicio de alta.
3. `frontend/src/pages/RegisterPage.tsx`, `frontend/src/services/api.ts`: conservar payload `first_name/last_name` y POST `/users/register-client`; agregar aviso y respuesta segura para 422 de política de contraseña; sin logs de secretos. Helper/test de #51 adaptados a este contrato.
4. Backend tests sintéticos de #51 aportan casos 2a/2b/2y, Unicode, límite de 72, malformed-hash HTTP 401 y login legacy >72, más validación 422 en **ambos** endpoints públicos, sin lookup ni escritura.
5. `pyproject.toml`, `uv.lock` y dos exports requirements tomados como **blobs idénticos** del viejo candidato #51, cuyo `pyproject` difería de develop solamente por bcrypt==4.3.0 y retirada de Passlib. Son artefactos ya generados por uv0.13.6 en [Actions 41475687897](https://github.com/mauedgar/FitFlow/actions/runs/41475687897), no hashes editados manualmente. Deben pasar `uv lock --check` y verificación exacta sobre **este nuevo SHA**; la prueba anterior no se transfiere.
6. Workflow especializado read-only con pruebas bcrypt/HTTP + matriz de compatibilidad 3.11-3.13 y rollback sintético; se evita repetir la suite backend/frontend completa, que corresponde a la CI baseline del PR Ready/develop. DRAFT baseline = SKIPPED / NOT_RUN, no full PASS.

## Aislamiento y riesgos

Sin modificar los PR DRAFT #48, #51, #83; #46 ya estaba CLOSED/UNMERGED. #44 es owner de normalización general y CPython; #47 es owner de Ruff/Pyright general; #49 es owner de schema; #36 de CI/reducción de duplicaciones; #40 de R007. Los cambios de este candidato limitan deps al mínimo indispensable para el bcrypt de #43; no se elige aquí Python3.15 de Product. No SQL de datos retenidos, migraciones, secretos, forced push, despliegue ni aceptación.

## Evidencia pendiente

Commit/tree de la rama nueva debe publicarse por recibo GitHub. Calificar Actions originales en ese SHA, registrar correctamente jobs `NOT_RUN`/FAIL y hacer independent WEB_INLINE IR con cobertura de cambios exactos. Los resultados antiguos 41482355644 y PR51 IR002 no validan esta composición ni cierran la Issue. Aceptación Product e integración **no automáticas**.

## Reconciliación del primer candidato y reparación puramente mecánica

La CI nativa original de `876cd4951a6a7148c88a308f54327c691de2bd42`, tree `966f178a8b218a98031727ef0d5bc086bf5a5198`, [run 42386446832](https://github.com/mauedgar/FitFlow/actions/runs/42386446832) terminó FAILURE, intento 1: 5/6 jobs SUCCESS (backend test/lock, compatibilidad Python3.11/3.12/3.13 con old/new sintéticos, frontend) y quality FAILURE por nueve diagnósticos Ruff I001/UP017/RUF100. Pyright especializado tuvo 0 errors/0 warnings. No declarar 0F/0A ni usar ese FAIL como PASS.

Reparación estrictamente mecánica y acotada para un commit sucesor: orden de imports en seguridad, esquema y prueba; eliminación de directivas `noqa` innecesarias; `timezone.utc` → `datetime.UTC` (objeto de zona UTC equivalente para CPython >=3.11), conservando exactamente la firma/flujo JWT, lógica bcrypt, transacciones, permisos y JSON de alta. CI exacta y reviewer del nuevo SHA siguen sin calificar. No tocar dato real ni ramas DRAFT concurrentes.
