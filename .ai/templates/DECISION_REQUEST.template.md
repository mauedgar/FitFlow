---
artifact: DECISION_REQUEST
schema_version: fitflow-decision-request/v1
task_id: "<TASK-ID>"
status: BLOCKED
created_at: "<ISO-8601>"
baseline_revision: "<revision>"
working_tree_fingerprint: "sha256:<hash>"
author_role: "<role>"
run_id: "<run-id>"
decision_owner: human
---

# Decisión

<Pregunta binaria o conjunto cerrado de alternativas.>

## Evidencia

- `<path/range/document_id>` — <hecho>.

## Opciones

| Opción | Impacto | Riesgo | Reversible |
| --- | --- | --- | --- |
| A | <impacto> | low/medium/high | yes/no |

## Recomendación

<opción + razón basada en evidencia>.

## Condición de desbloqueo

<decisión y actualización de TASK/PLAN requerida>.
