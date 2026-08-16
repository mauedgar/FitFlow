---
document_id: FF-AI-CONTEXT-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Estrategia de contexto

## Objetivo

Entregar al Coder el conjunto mínimo suficiente, trazable y actualizado para
resolver una tarea sin repetir la exploración.

## Capas

| Nivel | Contenido | Regla |
| --- | --- | --- |
| L0 | TASK y pregunta concreta | siempre |
| L1 | AGENTS + source of truth | siempre, compacto |
| L2 | docs/ADR relevantes | allowlist de TASK |
| L3 | inventario, XML, Repomix y retrieval | Explorer selecciona |
| L4 | lecturas directas de código/tests | evidencia final |
| L5 | diff + validación | review/cierre |

No incluir material humano, transcripts, archivos “por si acaso” ni resultados
sin baseline.

## Presupuesto inicial

| Scope | Máximo de contexto entregado al Coder |
| --- | ---: |
| backend | 8.000 tokens |
| frontend | 8.000 tokens |
| mixed | 12.000 tokens |
| docs/tooling | 4.000 tokens |

Un override requiere causa, nuevo máximo y registro en el Context Package. Los
valores se afinan con Phoenix y evaluaciones.

## Proceso del Explorer

1. Verificar scope, baseline y pregunta.
2. Leer inventario de directorios apropiado.
3. Consultar XML estructural y/o Repomix si está disponible.
4. Ejecutar búsqueda textual, Repomix o vectorial con filtros.
5. Leer directamente candidatos antes de citarlos.
6. Deduplicar y ordenar por necesidad.
7. Emitir Context Package validado.

## Orden de evidencia

Preferir definición, callers/callees, tests, configuración/contrato y doctrina
específica. Cada evidencia incluye `path`, rango, símbolo, hash, razón y fuente.

## Staleness

Si `baseline_revision` o `working_tree_fingerprint` difiere, el package es
`STALE` y no llega al Coder. Si un resultado vectorial apunta a un rango
inexistente, se descarta y se abre hallazgo de índice.

## Reintentos

Máximo dos solicitudes de contexto por ejecución. La tercera discrepancia
vuelve al Planner para recortar o reformular la tarea.
