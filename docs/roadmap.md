---
document_id: FF-ROADMAP-001
status: canonical
machine_context: true
version: 5.0
updated: 2026-08-18
---

# Roadmap de FitFlow

## Principio

El tooling reduce incertidumbre y repetición; no bloquea el MVP ni adquiere
autoridad sobre el producto.

## Producto

| Prioridad | Objetivo |
| --- | --- |
| P0 | preservar el baseline Sprint 6.8 y cerrar discrepancias críticas |
| P1 | MVP Cliente -> Agenda -> Sesión -> Reserva -> Front Desk |
| P2 | ampliar unit/integration/API/concurrency y estabilizar Alembic/frontend |
| P3 | entorno reproducible, logging, staging y beta controlada |
| P4 | asistencia avanzada, métricas, facturación y automatizaciones |

## Plataforma de desarrollo asistido

| Fase | Tareas | Gate de salida |
| --- | --- | --- |
| A - baseline/doctor | FF-AI-VNEXT-001-002 | baseline aceptada y entorno reproducible sin installs |
| B - contratos/runtime | FF-AI-VNEXT-003-004 | schemas, registries, State Machine y Run Store |
| C - adapters/contexto | FF-AI-VNEXT-005-006 | Project Profile, sync y ContextPackager compliant |
| D - decision/roles | FF-AI-VNEXT-007-009 | Router, Model Resolver, Explorer y Agent MVP medidos |
| E - endurecimiento | FF-AI-VNEXT-010 | fitness functions, CI y Workflow Observer |
| F - capacidades futuras | FF-AI-VNEXT-011-013 | retrieval, MCP y Temporal tras gates propios |

No avanzar de fase cuando el gate anterior está `FAIL`, `UNAVAILABLE` o
`BLOCKED` sin decisión explícita.

## Autonomía

Los agentes pueden explorar, editar scope acotado y ejecutar validaciones
permitidas. El desarrollador decide arquitectura/dominio, dependencias, seguridad,
migraciones destructivas, ampliación del MVP, promoción documental y aceptación
final.

## Paralelismo

Solo tareas sin ownership cruzado. La velocidad no justifica dos writers sobre
la misma ruta, contrato, dominio, DB/migración o documento canónico.
