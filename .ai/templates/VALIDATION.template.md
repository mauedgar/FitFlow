---
artifact: VALIDATION
schema_version: fitflow-validation/v1
task_id: "<TASK-ID>"
status: PASS
created_at: "<ISO-8601>"
baseline_revision: "<revision>"
working_tree_fingerprint: "sha256:<hash>"
author_role: validator
run_id: "<run-id>"
---

# Gates

| ID | CWD | Comando | Exit | Duración | Estado | Alcance |
| --- | --- | --- | ---: | ---: | --- | --- |
| V-1 | `<cwd>` | `<comando>` | 0 | 0s | PASS | <tests/checks> |

## Salida resumida

- V-1: <resultado verificable; sin logs extensos>.

## No ejecutado / unavailable

- `none` o <gate + causa + impacto>.

## Clasificación de fallos

- `none|implementation|environment|baseline|policy`.

## Recomendación

`PENDING_ACCEPTANCE|EXECUTE|EXPLORE|PLAN|BLOCKED`.
