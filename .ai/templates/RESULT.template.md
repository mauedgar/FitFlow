---
artifact: RESULT
schema_version: fitflow-result/v1
task_id: "<TASK-ID>"
status: PENDING_ACCEPTANCE
created_at: "<ISO-8601>"
baseline_revision: "<revision>"
working_tree_fingerprint: "sha256:<hash>"
author_role: orchestrator
run_id: "<run-id>"
---

# Resultado

<Qué se logró o por qué no se logró.>

## Archivos

- `<path>` — <cambio>.

## Evidencia

| Fuente | Estado | Referencia |
| --- | --- | --- |
| review | PASS | REVIEW.md |
| validation | PASS | VALIDATION.md |

## Criterios de aceptación

| Criterio | Estado |
| --- | --- |
| AC-1 | PASS/FAIL |

## Riesgos y deuda

- `none` o <riesgo/follow-up>.

## Impacto documental

- `none` o <documento + cambio propuesto>.

## Aceptación humana requerida

- revisar diff y evidencia;
- integrar mediante Git;
- promover índice/docs si corresponde;
- marcar `DONE` o devolver al estado indicado.
