# FitFlow — FF-LOCALvNext-001-adr-integrity — Plan de integridad de ADRs

**Estado:** PLANNING
**Dependencia:** ejecutar después de completar la Fase 3 de FF-LOCALvNext-000 (sus hallazgos son insumo).

## Objetivo
Verificar que cada ADR de docs/adr/ es consistente con la realidad ejecutable (código, tests, migraciones, configuración) y con su propio frontmatter (accepted / amended / accepted_pending_implementation / superseded / historical), detectando contradicciones como la detectada en ADR 0004 línea 16 (dice 'debe verificarse' sobre algo ya implementado).

## Insumos
- docs/adr/** completo.
- Inventarios previos explorer FF-LOCALv-000: 0002/0008 amended; 0007/0011/0012/0013 superseded; 0014-0017 accepted_pending_implementation.
- Código real por área afectada de cada ADR.
- Reglas de DocImpact vigentes.

## Pasos
1. Inventariar todos los ADR con id, título, estado de frontmatter y fecha.
2. Extraer claims verificables de cada ADR y contrastarlos contra código/tests reales con evidencia ruta:línea.
3. Clasificar: CONSISTENT / STALE_CLAIM / CONTRADICTORY / SUPERSEDED_OK / FORMAT_ISSUE.
4. Tabla: ADR | Estado declarado | Estado real observado | Evidencia | Acción propuesta (NONE / UPDATE_PROPOSAL / ARCHIVE_PROPOSAL / DEVELOPER_DECISION_REQUIRED).
5. Ninguna edición de ADR en este ciclo: toda corrección se propone vía DocImpact para aceptación del Developer.

## Prohibiciones
Estándar del repo: sin producto, sin commits/push/merge, sin promociones de estado, sin cambios semánticos automáticos.

## Entregable
.ai/tasks/FF-LOCALvNext-001-adr-integrity/RESULT.md con tabla completa, UPDATE_PROPOSAL priorizadas y veredicto único entre SPRINT_READY / CURATION_PARTIALLY_COMPLETED / DEVELOPER_DECISION_REQUIRED / WORKTREE_BLOCKED.
