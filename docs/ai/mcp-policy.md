---
document_id: FF-AI-MCP-001
status: planned
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Política MCP

## Gate de adopción

MCP se implementa después de que CLI, schemas, filtros y evaluación sean
estables. La primera versión es read-only.

## Herramientas iniciales

- `context_query`;
- `symbol_lookup`;
- `related_files`;
- `index_status`;
- `task_artifact_read`.

No exponer escritura de código, shell genérico, Git, instalación, secretos,
promoción de índices ni transición `DONE`.

## Seguridad

Cada llamada recibe task, scope, baseline y presupuesto; aplica allowlists de
rutas y límites de resultados. Logs redactan secretos y registran caller,
herramienta, filtros, revisión y IDs devueltos.

## Evolución

Una herramienta con efectos requiere threat model, autorización explícita,
idempotencia, rollback y ADR. La existencia de MCP en Codebase no justifica
habilitar escrituras.
