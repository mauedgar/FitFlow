# Contratos serializados

Todos los JSON Schema usan Draft 2020-12. El Markdown es una vista humana: un
parser extrae frontmatter y secciones a un objeto equivalente antes de validar.

| Ficha | Contrato |
| --- | --- |
| TASK | `task.schema.json` |
| PLAN | `plan.schema.json` |
| CONTEXT_REQUEST | `context-request.schema.json` |
| Context Package | `context-package.schema.json` |
| STATUS/transición | `status.schema.json` / `run-state.schema.json` |
| IMPLEMENTATION | `implementation.schema.json` |
| REVIEW | `review.schema.json` |
| VALIDATION | `validation.schema.json` |
| DECISION_REQUEST | `decision-request.schema.json` |
| INDEX_RUN/event | `index-run.schema.json` / `index-event.schema.json` |
| RESULT | `result.schema.json` |
| ownership | `ownership-lock.schema.json` |
| grafo XML | `structure-graph.xsd` |

El adapter rechaza campos desconocidos salvo donde el schema declare
extensibilidad explícita.
