---
document_id: FF-PY315-MIGRATION-DOCIMPACT-20261104-001
status: draft_validation_pending
date: 2026-11-04
product_acceptance: not_granted
source: mauedgar/FitFlow
---

# FitFlow — Python 3.15.2, candidato aislado

## Proveniencia

Fuente inicial PR #82 `4be0b32822a5cd2272db96b6402853804ef089b1`, tree `181e65f69584754f74708cf324b2876ccd87902c`. `develop@55772398c72f4c1a41862dccd79b04d38016dfcb`, SOT v5.3 blob `f36307af0777fd3b493792ad42115fec56ac44b3`. Issue #44 DoD y autorización: https://github.com/mauedgar/FitFlow/issues/44#issuecomment-6621650094.

## Write-set

`pyproject.toml`, `.python-version`, `uv.lock` y exports derivados, Dockerfiles runtime/test, CI Python relevante, ADR 0020 y este DocImpact. La rama de migración es independiente de PR #82 original; se conserva auth bcrypt nativo y la historia de revisiones. El bootstrap de uv opera **solo** sobre una rama de migración e intenta generar el lock y exports por uv, con guardas de identidad. No modifica `develop`.

## Gates

- G1: CPython3.15.2 exacto y fuente única: **PREPARADO**.
- G2: **PASS** para generación por uv e instalación de dependencias en CPython3.15.2: [run 41768133911](https://github.com/mauedgar/FitFlow/actions/runs/41768133911), base de generación `58d8249ac652966be106f3fee36fe9dcd3a73c4a`, commit generado `5a58bc868b4f38ad9930057511e12c2069ec30fc`, árbol `f0993eed448ae438f6583fda168c7d7bbbc53a9c`. Solo se alteraron `uv.lock`, `backend/requirements_backend.txt` y `backend/requirements_test.txt` mediante uv. Lock/export nuevos siguen sujetos a la CI/IR del candidato compuesto. No editar hashes manualmente. Si el bootstrap falla, preservar FAILED y diagnosticar, no repetir.
- G3: pruebas completas PG15/Redis7/Alembic, Python3.15.2, Ruff/Pyright, frontend, bcrypt histórico en entorno aislado: **NOT_RUN en candidato nuevo**.
- G4: Chrome E2E montado en nueva identidad con proceso/cleanup acotados: **PREPARADO / NOT_RUN**. Reparación de harness: diagnóstico de ChromeDriver, sesión 60s, deadline 180s, limpieza acotada, timeout externo 240s y workflow 6m. Sin prueba nueva todavía. Original PR82 run 41763004024 CANCELLED tras timeout WebDriver inicial, no reintentar el mismo run.
- G5: IR independiente exacta y aceptación competentemente autorizada antes de integrar: **NOT_RUN**.
- G6: CI postmerge y reconciliación Issue #44/otros: **NOT_RUN**.

A10 (ACK externos), A12 (infra TLS/IP), A13 (Redis retenido) siguen abiertos; no son eximidos por esta migración ni por pruebas sintéticas.

## Reconciliación de intentos de resolución

- [41767614256](https://github.com/mauedgar/FitFlow/actions/runs/41767614256) FAILED inicial al resolver `HEAD^` en checkout superficial: corregido mediante `fetch-depth: 0` y verificación de ancestralidad. No se relanzó.
- [41767760202](https://github.com/mauedgar/FitFlow/actions/runs/41767760202) FAILED al instalar Pydantic 2.11.10 / pydantic-core 2.33.2: PyO3 0.24.1 solo admite hasta 3.13, incompatibilidad real de Python3.15. No se eludió guard de PyO3.
- [41768017083](https://github.com/mauedgar/FitFlow/actions/runs/41768017083) FAILED resolución: Pydantic>=2.14.2 necesita typing-inspection>=0.4.4 y fuente fijaba 0.4.1.
- [41768133911](https://github.com/mauedgar/FitFlow/actions/runs/41768133911) SUCCESS original: uv regeneró lock y exports, instaló CPython3.15.2, comprobó imports y dependencias; publicación de un commit derivado verificada en GitHub. No se repitieron intentos terminales.

## Reparación exacta posterior de Python 3.15.2

- En PR #83 el primer CI exacto [41768605881](https://github.com/mauedgar/FitFlow/actions/runs/41768605881) exhibió la falta de `psycopg` en Alembic, y [su job quality](https://github.com/mauedgar/FitFlow/actions/runs/41768605881) detectó 16 diagnósticos Ruff por objetivo Python3.15. No se ignoraron reglas ni se usó un target-version falso.
- Se agregó `psycopg[binary]==3.3.6` (wheel CPython3.15), se actualizaron dos clases genéricas a PEP695, anotaciones forward-ref tipadas y AsyncGenerator; sus pruebas exactas aún deben calificar el nuevo sujeto.
- [Run de generación de lock 41769298850](https://github.com/mauedgar/FitFlow/actions/runs/41769298850) SUCCESS en fuente `65b4cc061f7111525d12d33b27bad4cc9becda25`: uv publicó `8a5e0db7ba3cb3d414c7043330fe0d6d5ca79202` / tree `0992b606dcda05a7af01c011f1999fa00e05d730`, **solo** `uv.lock`, requirements runtime y requirements test. Lock incluye Pydantic 2.14.2, pydantic-core 2.50.2, psycopg/psycopg-binary 3.3.6, SQLAlchemy y asyncpg compatibles. No hay hashes manuales.
- Los workflows del commit intermedio `65b4cc...` anteriores a la regeneración terminaron con FAIL por `uv lock --check` o backend desechable todavía no calificado; no son evidencia contra el lock regenerado ni PASS transferible.
- El workflow temporal `.github/workflows/python315-lock-bootstrap.yml`, con permiso `contents: write` exclusivamente en la rama de migración, **se excluye del candidato final** para no mantener un emisor privilegiado sin necesidad. Su historial y resultados quedan trazables; la generación futura corresponde a workflow/Product autorizado separado.
- G3 CI final y G5 IR siguen NOT_RUN hasta que una nueva revisión exacta del árbol final quede publicada y calificada.

## Reparación posterior a CI 374eebb3

En [PR83 CI Issue52 41769819316](https://github.com/mauedgar/FitFlow/actions/runs/41769819316) la suite de CPython 3.15.2 completó 398 PASS / 2 FAIL: `inspect.get_annotations` con PEP649 intentó evaluar `Client` de una relación SQLAlchemy importada solo bajo `TYPE_CHECKING`; el test de superficie de usuarios dependía de un prefijo mutable, aunque la comprobación positiva de HTTP de registro pasó. Se añade `from __future__ import annotations` a siete modelos con forward refs para preservar evaluación diferida sin silenciar Ruff y se hace que el test verifique el path real de registro y la ausencia de PUT/PATCH de usuarios sin depender del prefijo de configuración mutable.

En [Issue43 bcrypt CI 41769819384](https://github.com/mauedgar/FitFlow/actions/runs/41769819384) las pruebas de compatibilidad histórica/quality/frontend fueron SUCCESS; un test de rutas de usuarios dio el mismo FAIL y recibe la misma corrección, no un waiver.

En [schema CI 41769819336](https://github.com/mauedgar/FitFlow/actions/runs/41769819336) la instalación de requirements generados para 3.15.2 falló porque el workflow todavía elegía 3.11.17. Se alinea ese workflow a 3.15.2 sin cambiar el esquema ni el DB real.

Los otros workflows del candidato 374eebb3 fueron SUCCESS: browser montado, ingress Nginx/PG/Redis desechable, frontend/quality y baseline. Esos PASS históricos siguen vinculados a ese SHA, sin transferencia al nuevo candidato.

**Pendiente:** exact CI de esta nueva corrección, nueva IR independiente y aceptación/integración competente. A10/A12/A13 siguen abiertos.
