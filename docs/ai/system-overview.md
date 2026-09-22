---
document_id: FF-AI-SYSTEM-001
status: canonical
machine_context: true
version: 3.1
updated: 2026-09-22
---

# Integracion con el AI Core

## Proposito

Explicar solo la frontera necesaria entre FitFlow y el AI Core, sin duplicar la
arquitectura o el estado interno de Tecnotron-ai.

## Fronteras

| Capa | Ownership |
| --- | --- |
| producto, dominio, current-state y calidad | FitFlow |
| Project Profile, TASK, runs y contratos del consumidor | FitFlow |
| arquitectura, roadmap y estado interno del AI Core | Tecnotron-ai |
| tooling, contexto, adapters y Agent Runtime | Tecnotron-ai |
| workspace y sesion | Orca |
| aislamiento de escritura | Git worktree |
| planificacion, integracion y validacion | GitHub |

OpenCode es el Agent Runtime preferido actual detras de `AgentRuntimePort` y es
intercambiable. FitFlow no depende de una implementacion concreta del runtime de Tecnotron-ai.
La integracion consume contratos/configuracion explicitos del producto y
referencias al sistema de desarrollo mediante boundaries reemplazables; los
detalles del core se consultan en las fuentes listadas por `README.md`.
