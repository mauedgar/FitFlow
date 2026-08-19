---
document_id: FF-SOT-001
status: canonical
machine_context: true
version: 5.0
updated: 2026-08-18
---

# Source of Truth de FitFlow

## Proposito

Resolver contradicciones sin permitir que un resumen, un indice, un run o una
integracion externa adquieran autoridad sobre el sistema real.

## Capas de autoridad

| Orden | Capa | Autoridad |
| --- | --- | --- |
| 0 | realidad ejecutable | codigo, tests, configuracion, migraciones y estado reproducible |
| 1 | doctrina canonica | arquitectura, dominio, estado, calidad, proceso y ADR aceptados |
| 2 | control operativo | GitHub Project, Issues, PR, commits y resultados de Actions |
| 3 | artefactos de run | TASK espejo, route, context, execution, validation, review, doc impact y result |
| 4 | contexto derivado | inventarios, grafos, Repomix, repo-packager, embeddings, indices y caches |
| 5 | archivo | `docs/archive/`, informes fuente y material reemplazado |

Los tests solo prueban el comportamiento cubierto. Una decision aceptada pero
no implementada pertenece a doctrina, no a realidad ejecutable.

## Autoridad operacional unica

Cuando existe GitHub Issue sincronizada, la Issue es la TASK principal y
`.ai/tasks/<task_id>/TASK.md` es su espejo local. En ejecuciones locales sin
sincronizacion habilitada, el TASK aprobado es temporalmente la fuente
operativa. Nunca se editan ambas superficies como fuentes independientes.

Los JSON aceptados de `.ai/runs/<run_id>/` son la evidencia durable del run.
SQLite bajo `.ai/local/` es una proyeccion operacional regenerable. Comentarios,
checks y artifacts de GitHub son visualizacion o transporte, no una segunda
fuente con igual autoridad.

## Contexto derivado

Se autorizan paquetes `reduced`, `drill-down` y `expanded` generados por
`repo-packager`, snapshots Repomix, inventarios, grafos y retrieval evaluado.
Todo artefacto declara baseline o fingerprint, generador, exclusiones y hash.
Si no coincide con el working tree, es `STALE`.

Explorer decide que evidencia necesita. El empaquetador no decide suficiencia,
no amplia paths por cuenta propia y devuelve `PARTIAL` con omitted paths cuando
no puede cumplir la solicitud completa.

## Conflicto

1. Identificar fuentes, revisiones y ownership.
2. Verificar codigo y alcance real de tests.
3. Clasificar la contradiccion: estado, intencion, doctrina o artefacto stale.
4. Registrar `DecisionRequest` si cambia una decision durable.
5. Bloquear cuando resolverla amplie scope o riesgo.
6. Promover conocimiento durable solo mediante `DocImpact`, review y aceptacion
   del desarrollador.

## Estados documentales

- `canonical`: gobierna el presente.
- `accepted_pending_implementation`: decision aprobada no confirmada en codigo.
- `planned`: direccion futura no comprometida.
- `review_required`: evidencia incompleta o contradictoria.
- `historical`: trazabilidad sin autoridad.
- `superseded`: reemplazado por un documento identificado.

## OpenSpec

OpenSpec puede gobernar especificaciones y deltas funcionales cuando se adopte
para un bounded context. No gobierna el workflow, el estado del run, la
prioridad operativa ni la evidencia de implementacion.
