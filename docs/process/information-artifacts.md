---
document_id: FF-PROCESS-ARTIFACTS-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Fichas informativas y trazabilidad

## Regla común

Toda ficha incluye `artifact`, `schema_version`, `task_id`, `status`,
`created_at`, `baseline_revision`, `working_tree_fingerprint`, `author_role` y
`run_id`. Fechas ISO 8601; rutas relativas POSIX; estados enumerados; valores
desconocidos son `null`, no texto inventado.

## Matriz

| Ficha | Produce | Consume | Campos específicos |
| --- | --- | --- | --- |
| TASK | Orchestrator/persona | todos | objetivo, scope, risk, ownership, AC, docs |
| PLAN | Planner | Explorer/Coder | pasos, asignación, gates, fallos, decisiones |
| CONTEXT_REQUEST | Planner/Coder/Reviewer | Explorer | pregunta, scope, tipos de evidencia, budget |
| Context Package | Explorer | Coder/Reviewer | evidencia, relaciones, freshness, citations |
| STATUS | ejecución larga | Orchestrator/persona | estado, progreso, bloqueo, siguiente acción |
| IMPLEMENTATION | Coder | Reviewer/Validator | archivos, cambio, self-check, desviaciones |
| REVIEW | Reviewer | Orchestrator/Coder | hallazgos, severidad, decisión, ruta siguiente |
| VALIDATION | Validator | Orchestrator/persona | comandos, alcance, estado, output resumido |
| DECISION_REQUEST | cualquier rol | persona/Planner | contradicción, opciones, impacto, recomendación |
| INDEX_RUN | indexador | Explorer/operación | inputs, versiones, counts, deletes, checks |
| RESULT | Orchestrator | persona/docs | resumen, evidencia, riesgos, follow-ups |

## Severidad de hallazgo

- `critical`: integridad/seguridad/pérdida de datos; bloquea.
- `major`: criterio de aceptación o arquitectura incumplidos; bloquea.
- `minor`: defecto real no bloqueante si se registra follow-up.
- `note`: observación sin acción obligatoria.

## Serialización

El Markdown usa frontmatter YAML y se valida mediante parser. Intercambio entre
procesos usa JSON contra `.ai/contracts/`. XML estructural valida contra XSD.
El texto libre queda limitado a resumen, razón y evidencia; decisiones y estados
usan enums.

## Inmutabilidad

Una ficha aceptada no se reescribe para ocultar un fallo. Crear un nuevo `run_id`
o añadir una sección `amendments` con fecha y responsable.
