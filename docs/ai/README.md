---
document_id: FF-AI-INDEX-001
status: canonical
machine_context: true
version: 6.1
updated: 2026-08-25
---

# Integracion de FitFlow con AI Core

FitFlow-ai es la Source of Truth de arquitectura, roadmap, estado, tooling,
contexto, adapters, Agent Runtime e inferencia del AI Core. Este directorio no
mantiene una segunda descripcion canonica de esos componentes.

Fuentes canonicas externas: `docs/architecture.md`, `docs/current-state.md`,
`docs/implementation-roadmap.md`, `docs/compatibility-baseline.md` y
`docs/development-pipeline-adapter.md` del repositorio
`https://github.com/mauedgar/tecnotron-ai`, baseline documental `91a4697`.

## Clasificacion

| Documento | Clasificacion | Tratamiento |
| --- | --- | --- |
| `README.md` | KEEP | indice de ownership e integracion FitFlow |
| `system-overview.md` | KEEP | resumen minimo de la relacion producto/AI Core |
| `project-profile-and-openspec.md` | KEEP | configuracion e integracion especificas de FitFlow |
| `context-artifacts.md` | MIGRATION_PENDING | contratos/runs permanecen en FitFlow; separar defaults genericos sin romper consumers |
| `roadmap-vnext.md` | REFERENCE | puntero al roadmap canonico de FitFlow-ai |
| `references.md` | REFERENCE | referencias tecnicas no autoritativas |
| `ai-core-architecture.md` | SUPERSEDED | reemplazado por `FitFlow-ai/docs/architecture.md` |
| `fitflow-ai-layout.md` | SUPERSEDED | reemplazado por arquitectura y estado de FitFlow-ai |
| `development-pipeline.md` | SUPERSEDED | workflow generico propiedad de FitFlow-ai |
| `roles-and-model-routing.md` | SUPERSEDED | roles/routing genericos propiedad de FitFlow-ai |
| `registries.md` | SUPERSEDED | registries del core propiedad de FitFlow-ai |
| `context-strategy.md` | SUPERSEDED | estrategia generica de contexto propiedad de FitFlow-ai |
| `context-delivery-pipeline.md` | SUPERSEDED | ContextPackager/repo-packager propiedad de FitFlow-ai |
| `validation-pipeline.md` | SUPERSEDED | pipeline generico; FitFlow conserva `../quality-and-validation.md` |
| `cli-contract.md` | SUPERSEDED | CLI y Agent Runtime propiedad de FitFlow-ai |
| `opencode-operating-guide.md` | SUPERSEDED | adapter Agent Runtime propiedad de FitFlow-ai |
| `finops-policy.md` | SUPERSEDED | policy generica del core propiedad de FitFlow-ai |
| `observability-and-evaluation.md` | SUPERSEDED | observer/evals genericos propiedad de FitFlow-ai |
| `indexing-pipeline.md` | SUPERSEDED | retrieval generico propiedad de FitFlow-ai |
| `mcp-policy.md` | SUPERSEDED | politica MCP generica propiedad de FitFlow-ai |
| `codex-operating-guide.md` | ARCHIVE | guia historica ya superseded |
| `development-pipelines.md` | ARCHIVE | pipeline Jira/Aider historico |
| `indexer-pipeline.md` | ARCHIVE | Project Index historico |
| `mcp-future.md` | ARCHIVE | propuesta MCP historica |

`ARCHIVE` clasifica historia conservada en su ubicacion actual; no la promueve
a contexto activo. `SUPERSEDED` conserva trazabilidad mientras los links y
consumers se retiran. No se mueven archivos en esta reconciliacion.

Configuracion activa: `/.ai/config/`. Contratos de intercambio:
`/.ai/contracts/v2/`. El backlog `/.ai/backlog/vnext.yaml` es un espejo
`MIGRATION_PENDING`, no la autoridad del roadmap de AI Core.

## Limite entre producto y AI Core

Los schemas Pydantic bajo `backend/app/schemas/` y el OpenAPI de FastAPI son
contratos del producto web y permanecen bajo autoridad exclusiva de FitFlow.
No forman parte del AI Core.

Los JSON Schema bajo `/.ai/contracts/v2/` validan el intercambio operativo con
FitFlow-ai. Son el snapshot consumidor activo del baseline declarado: permiten
que FitFlow valide TASK, estado de run, routing, contexto, ejecucion, validacion,
review y evidencia sin importar el runtime del AI Core dentro del producto.

FitFlow-ai conserva autoridad sobre los contratos Zod ejecutables, la maquina
de estados generica, roles, routing, adapters e inferencia. FitFlow conserva su
Project Profile, TASK, runs, evidencia y configuracion especifica. Ninguna copia
local convierte a FitFlow en autoridad sobre la implementacion interna del Core.

La publicacion y sincronizacion de Zod hacia JSON Schema sigue
`MIGRATION_PENDING`; no existe aqui una decision canonica entre npm, submodulo u
otro mecanismo versionado. Hasta esa decision, `/.ai/contracts/v2/` no se
evoluciona unilateralmente y toda divergencia se registra sin inventar
compatibilidad. Esta restriccion no bloquea el desarrollo web del producto.
