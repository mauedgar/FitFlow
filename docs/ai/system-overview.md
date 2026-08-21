---
document_id: FF-AI-SYSTEM-001
status: canonical
machine_context: true
version: 3.0
updated: 2026-08-21
---

# Integracion con el AI Core

## Proposito

Explicar solo la frontera necesaria entre FitFlow y el AI Core, sin duplicar la
arquitectura o el estado interno de FitFlow-ai.

## Fronteras

| Capa | Ownership |
| --- | --- |
| producto, dominio, current-state y calidad | FitFlow |
| Project Profile, TASK, runs y contratos del consumidor | FitFlow |
| arquitectura, roadmap y estado interno del AI Core | FitFlow-ai |
| tooling, contexto, adapters y Agent Runtime | FitFlow-ai |
| workspace y sesion | Orca |
| aislamiento de escritura | Git worktree |
| planificacion, integracion y validacion | GitHub |

OpenCode es el Agent Runtime preferido actual detras de `AgentRuntimePort` y es
intercambiable. FitFlow no depende del runtime de FitFlow-ai. La integracion
consume configuracion y contratos versionados bajo `.ai/`; los detalles del
core se consultan en las fuentes listadas por `README.md`.
