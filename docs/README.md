---
document_id: FF-DOCS-INDEX-001
status: canonical
machine_context: true
version: 4.0
updated: 2026-08-16
---

# Documentación activa

| Pregunta | Documento |
| --- | --- |
| ¿Qué fuente prevalece? | `SOURCE_OF_TRUTH.md` |
| ¿Cómo está diseñado el producto? | `architecture.md` |
| ¿Qué está implementado? | `current-state.md` |
| ¿Qué reglas de negocio son estables? | `domain.md` |
| ¿Qué evidencia exige una tarea? | `quality-and-validation.md` |
| ¿Qué sigue? | `roadmap.md` |
| ¿Cómo operan los agentes? | `ai/` y `process/` |
| ¿Por qué se tomó una decisión? | `adr/` |

## Regla de inclusión

Los documentos con `machine_context: true` pueden ser seleccionados por una
tarea. `machine_context: false` impide su carga automática. La selección final
siempre se reduce a los documentos necesarios para el scope.

`archive/source-material/` contiene explicaciones e informes para personas. No
es una capa de instrucciones ni un corpus de recuperación.
