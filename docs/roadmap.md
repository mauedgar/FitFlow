---
document_id: FF-ROADMAP-001
status: canonical
machine_context: true
version: 4.0
updated: 2026-08-16
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
| A — baseline | FF-AI-000 | matriz de compatibilidad y decisiones sin upgrades implícitos |
| B — contexto estructural | FF-AI-001–002 | inventarios/Repomix y grafo Repomix reproducibles |
| C — recuperación | FF-AI-003–004 | índice incremental y 15–20 consultas evaluadas |
| D — orquestación | FF-AI-005 | máquina de estados, roles y adaptador ejecutables |
| E — evaluación/integración | FF-AI-006–008 | evals, MCP read-only y piloto low/medium |
| F — endurecimiento | FF-AI-009–012 | hooks, Phoenix, routing medido y locks de ownership |

No avanzar de fase cuando el gate anterior está `FAIL`, `UNAVAILABLE` o
`BLOCKED` sin decisión explícita.

## Autonomía

Los agentes pueden explorar, editar scope acotado y ejecutar validaciones
permitidas. Una persona decide arquitectura/dominio, dependencias, seguridad,
migraciones destructivas, ampliación del MVP, promoción documental y aceptación
final.

## Paralelismo

Solo tareas sin ownership cruzado. La velocidad no justifica dos writers sobre
la misma ruta, contrato, dominio, DB/migración o documento canónico.
