---
document_id: FF-AI-PROJECT-PROFILE-001
status: accepted_pending_implementation
machine_context: true
version: 1.0
updated: 2026-08-18
---

# Project Profile y OpenSpec

## Project Profile

`.ai/config/project-profile.yaml` adapta AI Core a FitFlow. Declara roots,
docs, arquitectura, scopes, ownership keys, risk signals, comandos, GitHub
labels, paths de runs y feature flags.

El core no contiene excepciones especificas de Booking, RRULE, frontend o
estructura de carpetas. Esas reglas pertenecen al perfil versionado.

## OpenSpec

OpenSpec se adopta como capa de especificacion funcional cuando su bootstrap y
compatibilidad se validen. Puede describir deltas, propuestas, tareas de cambio
funcional y archivo de specs aceptadas.

No reemplaza:

- GitHub Issue/TASK como unidad operativa;
- State Machine y retries;
- artefactos de run;
- validacion, review o aceptacion;
- docs/ADR para decisiones arquitectonicas.

## Estado

Node actual satisface el requisito conocido. La CLI OpenSpec no esta instalada
en el shell verificado. La adopcion es `accepted_pending_implementation`; no se
crea estructura OpenSpec hasta ejecutar el bootstrap task autorizado.
