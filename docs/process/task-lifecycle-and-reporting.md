---
document_id: FF-PROCESS-LIFECYCLE-001
status: canonical
machine_context: true
version: 2.0
updated: 2026-08-16
---

# Ciclo de tareas y reportes

## Separación de responsabilidades

| Sistema | Conserva |
| --- | --- |
| tracker | trabajo, prioridad, milestone y estado humano |
| TASK | contrato técnico |
| PLAN | estrategia y riesgos |
| Context Package | evidencia seleccionada |
| IMPLEMENTATION | cambios y self-check del Coder |
| REVIEW | inspección independiente |
| VALIDATION | comandos y resultados |
| RESULT | consolidación para aceptación |
| Git | diff, revisión e integración |
| docs | conocimiento durable aceptado |

## Estados

```text
BACKLOG -> READY -> PLAN -> EXPLORE -> EXECUTE -> REVIEW -> VALIDATE
         -> PENDING_ACCEPTANCE -> DONE
```

Estados laterales: `BLOCKED`, `BLOCKED_HIGH_RISK`, `CANCELLED`.

Transiciones de retorno:

- `REVIEW/VALIDATE -> EXPLORE`: falta contexto;
- `REVIEW/VALIDATE -> EXECUTE`: defecto localizado;
- cualquier estado activo `-> PLAN`: scope/doctrina/estrategia inválida;
- `BLOCKED -> READY`: una persona confirma que desapareció el bloqueo.

## Lanes

- `human`;
- `ai_orchestrated`;
- `mixed`;
- `undecided`.

El rol/modelo efectivo vive en el run, no como lane del tracker.

## Proporcionalidad

| Complejidad | Artefactos mínimos |
| --- | --- |
| trivial low | TASK + IMPLEMENTATION + VALIDATION + RESULT |
| medium | TASK + PLAN + Context Package + IMPLEMENTATION + REVIEW + VALIDATION + RESULT |
| larga | anteriores + STATUS e INDEX_RUN si aplica |

## Directorio de tarea

```text
.ai/tasks/<TASK-ID>/
  TASK.md
  PLAN.md
  CONTEXT_REQUEST.md
  STATUS.md
  IMPLEMENTATION.md
  REVIEW.md
  VALIDATION.md
  RESULT.md
  DECISION_REQUEST.md
  INDEX_RUN.md
```

Solo crear artefactos aplicables. No guardar transcripts extensos; usar
`.ai/local/` para temporal no versionado.

## Aceptación

El Orchestrator puede finalizar `PENDING_ACCEPTANCE`. Una persona revisa diff,
gates, riesgos y promoción documental; integra por Git y marca `DONE`.
