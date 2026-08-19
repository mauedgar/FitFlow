---
artifact: REVIEW_RESULT
schema_version: fitflow-review-result/v2
task_id: "<TASK-ID>"
run_id: "<run-id>"
created_at: "<ISO-8601>"
reviewer_role: reviewer
independent: true
verdict: PASS
next_state: DOC_SYNC
---

# Veredicto

`PASS|FAIL|REPLAN|BLOCKED`

## Hallazgos

| Severidad | Ruta/linea | Hallazgo | Accion |
| --- | --- | --- | --- |
| note | `N/A` | `none` | `none` |

## Evidencia revisada

- TASK y baseline;
- diff y fuente real;
- `ValidationResult`;
- ownership y document impact.
