---
artifact: RUN_RESULT
schema_version: fitflow-run-result/v2
task_id: "<TASK-ID>"
run_id: "<run-id>"
created_at: "<ISO-8601>"
status: COMPLETED
current_state: PENDING_ACCEPTANCE
---

# Resultado

<Resultado observable.>

## Criterios

| ID | Estado | Evidencia |
| --- | --- | --- |
| AC-1 | PASS | `<referencia>` |

## Artefactos

- `<path>`

## Riesgos y decisiones

- `none`

## Aceptacion del desarrollador

- revisar diff y evidencia;
- aceptar o devolver al estado indicado;
- integrar por Git y promover a `DONE`.
