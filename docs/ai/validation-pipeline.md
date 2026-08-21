---
document_id: FF-AI-PIPELINE-VALIDATION-001
status: superseded
machine_context: false
version: 2.0
updated: 2026-08-18
superseded_by: FitFlow-ai/docs/architecture.md
---

# Pipeline de validacion

## Orden

Validator se ejecuta despues de Execution y antes de Review. Review recibe
TASK, diff, fuente real y un `ValidationResult` ya observado.

## Gate registry

Cada gate define ID, comando, cwd, timeout, scope, risk applicability,
environment requirement y parser de salida. El workflow no inventa comandos.

## Estados

`PASS`, `FAIL`, `NOT_RUN`, `UNAVAILABLE`, `BLOCKED` y `N/A` conservan la
semantica de `docs/quality-and-validation.md`. Solo `PASS` satisface un gate
obligatorio.

## Routing

- `FAIL` atribuible al cambio: `ROUTING`.
- `FAIL` que invalida plan/doctrina: `PLANNING`.
- `UNAVAILABLE`: `BLOCKED` o aceptacion explicita si el gate no era obligatorio.
- riesgo alto descubierto: `BLOCKED_HIGH_RISK`.
- todos los gates obligatorios `PASS`: `REVIEWING`.

Un LLM puede resumir o diagnosticar una salida, pero no cambiar su estado.
