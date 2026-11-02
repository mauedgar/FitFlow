---
document_id: FF-ISSUE52-IR001-REPAIR-20261102-001
status: candidate_pending_independent_review
date: 2026-11-02
product_acceptance: not_granted
merge_authorized: false
---

# FitFlow — PR #52 IR001 reparación independiente

## Autoridad y aislamiento

- Doctrina: `develop@c15bdefc766dfa42fa2b5b86b679ed3bf0f5a47d`, tree `9a2033e862535d6c0dc72b97a284811b1f401175`, SOT v5.3 blob `f36307af0777fd3b493792ad42115fec56ac44b3`.
- Sujeto original inmutable: [PR #52](https://github.com/mauedgar/FitFlow/pull/52) `cdfb61a32bf3ed2443656a1b4625eac91a7b7e7e` / tree `da941bd3c6af56f51b7bf4e3da25706b560311f2`, [IR001 2F/2A](https://github.com/mauedgar/FitFlow/pull/52#issuecomment-6583492960), NO_RECOMMEND.
- [Ruling Product](https://github.com/mauedgar/FitFlow/pull/52#issuecomment-6583554101) permite reparaciones F01/F02/A01/A02 en rama exclusiva `security/fitflow-pr52-ir001-repair-20261102-001`. El ruling no acepta el candidato ni autoriza merge.
- La identidad final del candidato se determina por el HEAD y tree del nuevo PR; este documento no se autorreferencia con un SHA que cambiaría al editarlo.

## Delta de seguridad y comportamiento

- **F01 CRITICAL**: el modelo `PublicUserRegistration` limita `role` a `client`, FastAPI devuelve 422 por `admin`, `teacher`, `front_desk`, `null` u otro valor, y el endpoint crea un `UserCreate(role=client)` nuevo en el servidor, sin copiar el rol de entrada. Las cuentas privilegiadas solo pueden existir por provisioning autorizado externo al endpoint público; no se habilita ruta de bootstrap anónimo.
- **F02 HIGH**: `/users/me` y `/users/me/stats` dependen del JWT validado y de la cuenta ORM propia, no de `user_id` en path/query ni de un DTO de guard. Carga explícita de Person, Client.user/bookings/session y Teacher.class_schedules; proyecciones por `isinstance` para herencia real; perfiles ausentes retornan null/cero, sin lecturas cruzadas.
- **A01 MEDIUM**: prueba real PostgreSQL 15 con dos transacciones, espera observable `pg_stat_activity/pg_blocking_pids`, commit y rollback, `FOR UPDATE OF users, persons, clients`, lectura posterior y escritura serializada; base `fitflow_test` desechable.
- **A02 LOW**: helper `loginUser` usa `/auth/token`, igual que `classService.login` activo; test Node valida rutas montadas y prohíbe helper obsoleto.
- No se modifican datos reales, staging ni contraseñas de usuarios. Se conserva bcrypt4.3, compatibilidad heredada, 72 bytes UTF-8/no NUL/422, `asyncpg==0.32.0`, Python3.11–3.13 y hashes del lock. No cambios a revisiones Alembic ni schema read-only.

## Validación y aceptación

- [Workflow candidato](https://github.com/mauedgar/FitFlow/blob/security/fitflow-pr52-ir001-repair-20261102-001/.github/workflows/issue52-ir001-repair-verify.yml) debe ejecutar SHA/tree exactos: backend PostgreSQL15/Redis7, Alembic y suite completa por Python3.11/3.12/3.13; Ruff/Pyright; frontend Node22 test y build. Se califica por cada SHA nuevo; los 906 tests del PR52 anterior **no** se transfieren.
- La IR independiente WEB_INLINE nueva debe ser 0 findings y 0 advisories para recomendar aceptación Developer; incluso en ese caso, PR permanece DRAFT y no se integra sin aceptación explícita.
- Issue #37 staging/TLS desplegado y E2E siguen NOT_RUN; TLS sintético no satisface staging real.
