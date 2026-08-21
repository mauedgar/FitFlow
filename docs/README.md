---
document_id: FF-DOCS-INDEX-001
status: canonical
machine_context: true
version: 5.1
updated: 2026-08-21
---

# Documentacion activa

| Pregunta | Documento |
| --- | --- |
| Que fuente prevalece | `SOURCE_OF_TRUTH.md` |
| Como esta disenado el producto | `architecture.md` |
| Que esta implementado | `current-state.md` |
| Que reglas de negocio son estables | `domain.md` |
| Que evidencia exige una tarea | `quality-and-validation.md` |
| Que sigue en el producto | `roadmap.md` |
| Como migra v4 a vNext | `MIGRATION.md` |
| Como se integra FitFlow con AI Core | `ai/README.md` |
| Como opera AI Core | repositorio FitFlow-ai, segun `SOURCE_OF_TRUTH.md` |
| Por que se tomo una decision | `adr/` |

## Regla de inclusion

Solo documentos `machine_context: true` pueden seleccionarse automaticamente.
La seleccion se limita a `required_docs` y evidencia del scope.

`archive/source-material/` contiene informes fuente y documentos para
desarrolladores en `.md`. No es una capa de instrucciones ni un corpus de
retrieval.
