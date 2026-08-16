---
document_id: FF-AI-OBS-001
status: accepted_pending_implementation
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Observabilidad y evaluación

## Phoenix

Phoenix es el backend inicial de trazas. La unidad de correlación es
`task_id/run_id`. Spans mínimos:

- `plan`;
- `explore.query` y `explore.package`;
- `model.invoke`;
- `review`;
- `validation.command`;
- `index.discover`, `parse`, `embed`, `upsert`, `verify`;
- `human.acceptance`.

Capturar modelo efectivo, razonamiento, latencia, tokens/costo disponible,
revisión, IDs de evidencia y estados. No capturar secretos ni código completo
si los IDs/hash son suficientes.

## Métricas

| Dimensión | Métrica |
| --- | --- |
| contexto | tokens, duplicación, staleness, context requests |
| retrieval | recall/precision top-k, citas verificadas |
| ejecución | first-pass review, retrabajo, scope violations |
| validación | pass/fail/not-run/unavailable por gate |
| modelo | éxito por rol/tipo/riesgo, latencia y costo |
| índice | tiempo, nodos, deletes, parse failures y drift |

## Golden set

Mantener 15–20 consultas representativas: arquitectura, dominio, callers,
tests, configuración y cambios mixtos. Cada fixture declara paths/símbolos
esperados, evidencia prohibida y presupuesto.

## Promptfoo

Incorporar después de estabilizar fixtures y outputs. Evaluar prompts, modelos y
fallbacks con los mismos contratos. No usar una nota LLM como único juez de
correctitud; combinar schemas, expected evidence y checks deterministas.

## Umbral de autonomía

No ampliar a tareas altas. Para ampliar tareas low/medium, exigir tendencia
estable en varias ejecuciones, cero violaciones críticas y revisión humana de
las métricas.
