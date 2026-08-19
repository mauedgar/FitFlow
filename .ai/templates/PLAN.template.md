---
artifact: PLAN
schema_version: fitflow-plan/v2
task_id: "<TASK-ID>"
run_id: "<run-id>"
status: PASS
created_at: "<ISO-8601>"
author_role: developer_planner
risk: low
ownership_keys: []
---

# Resultado esperado

<Resultado observable.>

## Pasos

| ID | Responsable | Accion | Input | Output | Gate |
| --- | --- | --- | --- | --- | --- |
| P1 | router | `<accion>` | `<input>` | `<output>` | `<condicion>` |

## Validaciones

| Gate | Comando/inspeccion | Resultado requerido |
| --- | --- | --- |
| targeted | `<comando>` | PASS |

## Rutas de fallo

| Condicion | Transicion |
| --- | --- |
| contexto insuficiente | EXPLORING |
| implementacion o validacion fallida | ROUTING |
| doctrina/scope invalido | PLANNING |
