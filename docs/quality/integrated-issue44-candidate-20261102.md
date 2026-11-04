---
document_id: FF-INTEGRAL-DEPS-QUALITY-AUTH-CANDIDATE-20261102-001
status: candidate_pending_exact_validation_and_ir
date: 2026-11-02
product_acceptance: not_granted
merge_authorized: false
---

# FitFlow — candidato de reconciliación integral de dependencias, calidad y autenticación

## Autoridad y fuentes

- SOT canónica: `mauedgar/FitFlow/develop@c15bdefc766dfa42fa2b5b86b679ed3bf0f5a47d`, tree `9a2033e862535d6c0dc72b97a284811b1f401175`, `docs/SOURCE_OF_TRUTH.md` v5.3 (blob `f36307af0777fd3b493792ad42115fec56ac44b3`). No modificación de SOT ni aceptación en esta rama.
- Base de trabajo exclusiva: PR #48 `d5418053a4d48e49d433d5284cce4a2df4282be8`, tree `923c1eec14d52c73f7f1d65ec00754cd64535ec9`; la rama original PR #48 no se alteró.
- Fuente de normalización: PR #46 `abed954362112e9467ed94b7bd560cc09677b827`, árbol `5a0f153b9ee0c998e66f006eb7dc2d39581368dc`; exclusivamente `backend/pytest.ini`, `docs/quality-and-validation.md` y `pyproject.toml`, este último reconciliado con bcrypt.
- Fuente de autenticación: PR #51 `b77d21c91a353a3dea90c61979954f0edefe6b02`, árbol `54e0f137e083596f2ed690159361c6ea0625f18b`; 13 paths no relacionados con lock/requirements, incluida implementación y tests de bcrypt, política de passwords y UX frontend.
- Issue #49 seleccionó variante de schema de PR #48 y preservó PR #50 DRAFT como alternativa SUPERSEDED_FOR_SELECTION / no integrada. No se transfieren reviews de un candidato a otro.

## Composición y límites

- `pyproject.toml` es autoridad de versiones: Python >=3.11,<3.14, `asyncpg==0.32.0`, `bcrypt==4.3.0`, pytest 9.2.0, pytest-asyncio 1.4.1, Ruff 0.17.3 y Pyright 1.1.414. Passlib se elimina del candidato compuesto.
- `uv.lock` y `backend/requirements_backend.txt` / `backend/requirements_test.txt` fueron regenerados **desde ese único manifiesto**, sin editar manualmente hashes, mediante uv 0.13.6 en runner GitHub temporal [41486665601](https://github.com/mauedgar/FitFlow/actions/runs/41486665601), SUCCESS. Digests de texto generados: lock `05af00a45e2d477cf457862435759b63ba82108c1e7cbe3649578f7abb067f2d`, runtime `6e9cae7e1079e6f3b2323d0dbe34a6bbe44166e99b56ec42141474235ec4d331`, tests `d4cbf367904e94c6d16c7bdf8e2bf945aca6aed2a2aa7c43bcf27d94889e1a1d`. Generador CI temporal retirado de este árbol.
- Se copió la implementación bcrypt y `backend/app/schemas/user.py` de PR #51 sobre PR #48; esas rutas tenían ownership coincidente y **deben ser sometidas a calidad y pruebas combinadas**, no basta con considerar sus revisiones independientes. Si es necesaria una reparación de imports/typing, queda sujeta a contrato API y pruebas.
- PR #48 porta las correcciones CRUD/row-lock/ORM, test de regresión, migraciones históricas sin alteración del grafo/DDL y workflow `update-schema.yml` read-only con artifact y sin auto-commit; este conjunto queda sujeto a tests integrados.
- Política Product explícita propuesta en [Issue43](https://github.com/mauedgar/FitFlow/issues/43#issuecomment-6582023324): nuevas contraseñas <=72 bytes UTF-8 sin NUL; HTTP 422 para nuevas entradas inválidas, sin truncamiento; hashes bcrypt heredados verificables, sin reset ni migración de usuarios, y con rollback sintético. **Material change** en validación, todavía no aceptado por Developer.
- Riesgo de staging real TLS permanece en Issue #37. [TLS efímero](https://github.com/mauedgar/FitFlow/actions/runs/41388057209) y [Docker](https://github.com/mauedgar/FitFlow/actions/runs/41387764179) calificaron árboles individuales anteriores, NO este candidato ni staging desplegado.
- Issue #43, #44, #47, #49 siguen OPEN, PR #46/#48/#50/#51 DRAFT y no integradas.

## Gates pendientes

1. Revalidar el árbol exacto compuesto: `uv lock --check`, equivalencia de ambos exports, `pip check`, Python 3.11/3.12/3.13, pytest completo contra PostgreSQL/Redis efímeros y Alembic, Ruff/Pyright sin supresión y artefactos schema/metadata.
2. Verificar bcrypt heredado y rollback inverso, HTTP 422/401, permisos/seguridad y frontend build, y calificar Docker/TLS si procede sin tocar staging real.
3. Reconciliar cualquier choque semántico de `security.py`, `schemas/user.py` o dependencias en un commit nuevo, con DoD y revisión independiente sobre su SHA/tree propio.
4. Independent Review WEB_INLINE independiente, **0 findings y 0 advisories antes de recomendar aceptación**. No merge, deploy, cierre de Issues o TaskCycle por defecto.

La prueba de cada subcomponente no se transfiere automáticamente a este árbol. Ninguna operación sobre datos reales o credenciales está autorizada.
