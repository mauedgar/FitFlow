---
document_id: FF-DOCS-INDEX-001
status: canonical
machine_context: true
version: 5.0
updated: 2026-08-18
---

# Documentacion activa

| Pregunta | Documento |
| --- | --- |
| Que fuente prevalece | `SOURCE_OF_TRUTH.md` |
| Como esta disenado el producto | `architecture.md` |
| Que esta implementado | `current-state.md` |
| Que reglas de negocio son estables | `domain.md` |
| Que evidencia exige una tarea | `quality-and-validation.md` |
| Que sigue | `roadmap.md` y `ai/roadmap-vnext.md` |
| Como migra v4 a vNext | `MIGRATION.md` |
| Como opera AI Core | `ai/` |
| Por que se tomo una decision | `adr/` |

## Regla de inclusion

Solo documentos `machine_context: true` pueden seleccionarse automaticamente.
La seleccion se limita a `required_docs` y evidencia del scope.

`archive/source-material/` contiene informes fuente y documentos para
desarrolladores en `.docx`. No es una capa de instrucciones ni un corpus de
retrieval.
