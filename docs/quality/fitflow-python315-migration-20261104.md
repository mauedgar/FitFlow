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
- G2: `uv lock --upgrade`, `uv export --locked` para runtime/dev y `uv sync --locked`: **PENDIENTE DE EVIDENCIA NATIVA**. No editar hashes manualmente. Si el bootstrap falla, preservar FAILED y diagnosticar, no repetir.
- G3: pruebas completas PG15/Redis7/Alembic, Python3.15.2, Ruff/Pyright, frontend, bcrypt histórico en entorno aislado: **NOT_RUN en candidato nuevo**.
- G4: Chrome E2E montado en nueva identidad con proceso/cleanup acotados: **NOT_RUN**. Original PR82 run 41763004024 CANCELLED tras timeout WebDriver inicial, no reintentar el mismo run.
- G5: IR independiente exacta y aceptación competentemente autorizada antes de integrar: **NOT_RUN**.
- G6: CI postmerge y reconciliación Issue #44/otros: **NOT_RUN**.

A10 (ACK externos), A12 (infra TLS/IP), A13 (Redis retenido) siguen abiertos; no son eximidos por esta migración ni por pruebas sintéticas.
