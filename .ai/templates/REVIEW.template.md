---
artifact: REVIEW
schema_version: fitflow-review/v1
task_id: "<TASK-ID>"
status: PASS
decision: PASS
created_at: "<ISO-8601>"
baseline_revision: "<revision>"
working_tree_fingerprint: "sha256:<hash>"
author_role: reviewer
run_id: "<review-run-id>"
reviewed_run_id: "<coder-run-id>"
independent_execution: true
---

# Veredicto

`PASS|REQUEST_CONTEXT|REQUEST_CHANGES|REPLAN|BLOCKED`

## Criterios

| Criterio | Estado | Evidencia |
| --- | --- | --- |
| AC-1 | PASS/FAIL | `<path/range>` |

## Hallazgos

| ID | Severidad | Ruta/rango | Hallazgo | Acción |
| --- | --- | --- | --- | --- |
| R-1 | minor | `<path:line>` | <hecho> | <acción> |

## Scope y arquitectura

- scope: `PASS|FAIL`
- architecture: `PASS|FAIL|N/A`
- tests proposed: `SUFFICIENT|INSUFFICIENT`

## Siguiente estado

`VALIDATE|EXPLORE|EXECUTE|PLAN|BLOCKED`.
