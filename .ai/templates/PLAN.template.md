---
artifact: PLAN
schema_version: fitflow-plan/v1
task_id: "<TASK-ID>"
status: PASS
created_at: "<ISO-8601>"
baseline_revision: "<revision>"
working_tree_fingerprint: "sha256:<hash>"
author_role: planner_audit
run_id: "<run-id>"
risk: low
assigned_coder: coder_b
ownership_keys: []
---

# Resultado esperado

<Una oración observable.>

## Supuestos verificados

- <hecho + evidencia>

## Decisiones requeridas

- `none` o referencia a `DECISION_REQUEST.md`.

## Pasos

| ID | Responsable | Acción | Input | Output | Gate |
| --- | --- | --- | --- | --- | --- |
| P1 | explorer | <acción> | <input> | <output> | <condición> |

## Validaciones

| Gate | Comando/inspección | Resultado requerido |
| --- | --- | --- |
| targeted | `<comando>` | PASS |

## Rutas de fallo

| Condición | Transición |
| --- | --- |
| contexto insuficiente | EXPLORE |
| defecto localizado | EXECUTE |
| doctrina/scope inválido | PLAN + decisión |
