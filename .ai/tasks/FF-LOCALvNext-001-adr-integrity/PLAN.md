# FitFlow - FF-LOCALvNext-001-adr-integrity - Plan de integridad de ADR

**Estado:** BLOCKED
**Riesgo:** `medium`
**Dependencia bloqueante:** completar correctamente la Fase 3 definida en
`.ai/tasks/FF-LOCALv-000/PLAN.md`, seccion
`Fase 3 - Reconciliacion de tasks`.

La dependencia no se refiere al Paso 3 de
`.ai/tasks/FF-LOCALvNext-000/PLAN.md`.

## Gate de entrada

Esta task permanece `BLOCKED` hasta que:

1. la Fase 3 de `FF-LOCALv-000` termine con evidencia aceptable;
2. sus `REVIEW.md`, `VALIDATION.md` y `RESULT.md` actuales esten disponibles;
3. el Developer acepte usar esos hallazgos como insumo;
4. se materialice un `TASK.md` propio con baseline, branch, worktree, risk,
   ownership, allowed write scope, criterios y validaciones.

Si el ciclo previo concluye `WORKTREE_BLOCKED` o
`DEVELOPER_DECISION_REQUIRED`, esta task continua `BLOCKED`.

## Objetivo futuro

Verificar que cada ADR de `docs/adr/` sea consistente con realidad ejecutable y
con su frontmatter, sin editar automaticamente conocimiento durable.

## Ownership futuro

| Actor | Responsabilidad |
| --- | --- |
| Developer | aceptar decisiones, DocImpact y cambios semanticos |
| Lifecycle | preparar branch/worktree task-scoped y verificar baseline/limpieza |
| Agente ejecutor | inventario y contraste dentro del scope aprobado |
| Validator | comprobaciones deterministas y reproducibles |
| Reviewer | revision semantica independiente |

Ownership propuesto para materializar en `TASK.md` antes de ejecutar:

- `path:.ai/tasks/FF-LOCALvNext-001-adr-integrity/**`;
- `doc:docs/adr/**` en modo de propuesta, sin escritura canonica automatica;
- `domain:sprint-6.8-adr-integrity`.

## Insumos futuros

- `docs/adr/**` completo;
- resultado aceptado de la Fase 3 de `FF-LOCALv-000`;
- codigo, tests, migraciones y configuracion por area afectada;
- reglas FitFlow vigentes de DocImpact;
- `TECNOTRON_REVIEW.md` solo como cuarentena cross-repo, nunca como autoridad.

## Pasos futuros

1. inventariar ADR con id, titulo, estado y fecha;
2. extraer claims verificables y contrastarlos contra evidencia ejecutable;
3. clasificar `CONSISTENT`, `STALE_CLAIM`, `CONTRADICTORY`, `SUPERSEDED_OK` o
   `FORMAT_ISSUE`;
4. proponer `NONE`, `UPDATE_PROPOSAL`, `ARCHIVE_PROPOSAL` o
   `DEVELOPER_DECISION_REQUIRED`;
5. ejecutar validacion determinista disponible;
6. obtener review semantica independiente;
7. producir `REVIEW.md`, `VALIDATION.md` y `RESULT.md` del run actual;
8. dejar cualquier cambio canonico como DocImpact para aceptacion Developer.

## Prohibiciones

- no ejecutar antes de cerrar correctamente la Fase 3 de `FF-LOCALv-000`;
- no editar ADR en el ciclo de auditoria;
- no implementar producto;
- no promover estados;
- no hacer merge o push;
- no inventar evidencia;
- no corregir desde FitFlow arquitectura o estado interno de Tecnotron.

## Entregable futuro

El bundle de ejecucion contiene `TASK.md`, `PLAN.md`, `REVIEW.md`,
`VALIDATION.md` y `RESULT.md`, claramente asociado al nuevo baseline y run. Las
representaciones machine-readable se usan solo si el contrato FitFlow vigente
admite la identidad sin copiar contratos internos de Tecnotron.
