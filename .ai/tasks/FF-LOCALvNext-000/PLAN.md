# FitFlow - FF-LOCALvNext-000 - Plan previo a Fase 3

**Estado de la futura Fase 3:** PLANNING; no ejecutar hasta aceptacion del Developer
**Task:** `.ai/tasks/FF-LOCALvNext-000/TASK.md`
**Riesgo:** `medium`
**Branch:** `feat/FF-NEXT-000`
**Worktree:** `C:/Users/maued/orca/workspaces/FitFlow/feat-FF-NEXT-000`
**Baseline recreado:** `develop@046fa1f34d3886c3dbdd4a2f6a5064c0fb2a759e`

## Fase gobernada

En este plan, "Fase 3" significa exclusivamente:

`.ai/tasks/FF-LOCALv-000/PLAN.md` -> `Fase 3 - Reconciliacion de tasks`.

No significa el Paso 3 de este documento. Este ciclo corrige y prepara la
ejecucion; no realiza la reconciliacion de `FF-LOCAL-001..010`.

## Objetivo

Dejar un baseline verificable y un contrato operativo minimo para desarrollar,
en un ciclo posterior, la Fase 3 de reconciliacion de las diez tasks locales sin
inventar evidencia ni transferir a FitFlow responsabilidades de Tecnotron.

## Reconstruccion del baseline

| Evidencia | Resultado |
| --- | --- |
| Estado inicial | `develop` limpio en `046fa1f34d3886c3dbdd4a2f6a5064c0fb2a759e` |
| Rama/worktree antes de recrear | `feat/FF-NEXT-000` ausente; destino de worktree libre |
| Procedencia historica | `git -C C:/Proyectos-Web/FitFlow reflog --all`: checkout `develop -> feat/FF-NEXT-000` en `eeb8edc86ef8b7ec11fdf78e3ae8a68602438390` |
| Trabajo exclusivo recuperable | no se encontraron commits propios de la feature entre ese checkout y el regreso a `develop` |
| Estrategia | recrear la rama desde el `develop` vigente, sin rebase, merge, reset ni perdida de trabajo |
| Resultado | branch y worktree creados en `046fa1f`; `merge-base(feat/FF-NEXT-000, develop) = 046fa1f` |
| Limpieza inicial | `git status --short --branch` mostro el worktree limpio inmediatamente despues de crearlo |

Los cambios documentales de este ciclo son `task_dirty` esperado. Antes de
iniciar la Fase 3, Lifecycle debe comprobar otra vez branch, SHA y limpieza tras
la aceptacion e integracion de esta reconciliacion documental.

## Precedencia de evidencia

1. codigo;
2. tests;
3. migraciones;
4. configuracion ejecutable;
5. documentacion canonica aplicable;
6. TASK y criterios aceptados;
7. artefactos de ejecucion: `REVIEW`, `VALIDATION` y `RESULT`;
8. contexto derivado.

`RESULT.md` resume o registra evidencia. No convierte en verdadera una
afirmacion contradicha por codigo, tests, migraciones o configuracion.

## Ownership

| Actor | Responsabilidad |
| --- | --- |
| Developer | arquitectura, excepciones, secretos y `.env`, decisiones de DB, aceptacion final e integracion |
| Lifecycle | resolver baseline, crear/verificar branch y worktree, registrar asociacion, comprobar limpieza y ejecutar gates Git deterministas |
| Agente ejecutor | analizar las tasks y escribir solo artefactos task-scoped autorizados |
| Validator | ejecutar validaciones deterministas/reproducibles y normalizar estados |
| Reviewer | realizar revision semantica independiente; no es el mismo acto logico que la implementacion |

Ownership keys y allowed write scope de este run preparatorio se encuentran
resueltos en `.ai/tasks/FF-LOCALvNext-000/TASK.md`. No incluyen los bundles
historicos `FF-LOCAL-001..010`: la futura Fase 3 debe adquirir esas rutas de
forma explicita antes de escribir. No hay ownership para backend, frontend,
`.env`, DB, migraciones ni documentacion canonica.

## Lifecycle FitFlow provisional

FitFlow adopta el siguiente patron reusable expresado en terminos propios del
producto:

```text
TASK aprobada
-> branch de task
-> worktree task-scoped
-> baseline y write scope registrados
-> trabajo semantico acotado
-> VALIDATION deterministica
-> REVIEW independiente
-> PENDING_ACCEPTANCE
-> aceptacion Developer
-> integracion verificada
-> sincronizacion documental aplicable
-> DONE
-> cleanup seguro
```

Reglas del ciclo:

- cada unidad ejecutable tiene identidad, baseline, risk, ownership, alcance,
  criterios de aceptacion y validaciones;
- operaciones Git mecanicas pertenecen a Lifecycle, no al agente ejecutor;
- `PASS`, `FAIL`, `NOT_RUN` y `UNAVAILABLE` conservan significados distintos;
- validacion, review, aceptacion e integracion no se infieren entre si;
- solo el Developer puede autorizar la integracion y la promocion terminal;
- la automatizacion generica del lifecycle, adapters, registries y contratos
  internos del AI Core permanecen bajo ownership de Tecnotron/FitFlow-ai.

La documentacion canonica actual de FitFlow no se sobrescribe en este ciclo. Las
incompatibilidades se registran para una correccion posterior acotada.

## Bundle de evidencia

### Tasks nuevas y ejecuciones futuras

| Artefacto | Regla FitFlow |
| --- | --- |
| `TASK.md` | obligatorio antes de trabajo semantico; identidad, riesgo, ownership, baseline, write scope y criterios |
| `PLAN.md` | obligatorio cuando el riesgo o la complejidad requieren descomposicion y gates explicitos |
| `VALIDATION.md` | evidencia determinista del run actual, con comando, cwd, salida y `PASS/FAIL/NOT_RUN/UNAVAILABLE` |
| `REVIEW.md` | review semantica independiente del run actual |
| `RESULT.md` | consolidacion del run; distingue ejecucion, validacion, review, aceptacion e integracion |

Los JSON machine-readable de `.ai/runs/<run_id>/` se usan cuando los contratos
FitFlow vigentes admiten la identidad y el artefacto. No se copian contratos de
Tecnotron. El identificador historico `FF-LOCALvNext-000` no satisface el patron
mayusculo de `.ai/contracts/v2/common.schema.json`; este ciclo no renombra la
task ni altera el schema y reporta esa representacion como `UNAVAILABLE`.

### Tasks historicas `FF-LOCAL-001..010`

- preservar `TASK.md`, `RESULT.md` y cualquier evidencia existente;
- registrar como `MISSING_HISTORICAL`, no fabricar, artefactos que nunca
  existieron;
- la futura Fase 3 puede crear `REVIEW.md` y `VALIDATION.md` como evidencia de
  revalidacion actual, con fecha, baseline y atribucion del nuevo ciclo;
- esos archivos no se presentan como evidencia de la ejecucion original;
- no actualizar el `RESULT.md` historico automaticamente;
- si el lifecycle y el scope autorizan una actualizacion, conservar de forma
  explicita el resultado historico y separar la revalidacion actual;
- una promocion de estado requiere decision previa del Developer y evidencia
  reproducible.

## Decisiones registradas

| Tema | Estado | Decision |
| --- | --- | --- |
| Fase 3 correcta | RESUELTA | `.ai/tasks/FF-LOCALv-000/PLAN.md`, seccion `Fase 3 - Reconciliacion de tasks` |
| Baseline | RESUELTA | recrear `feat/FF-NEXT-000` desde `develop@046fa1f`; no ejecutar sobre `develop` |
| Riesgo | RESUELTA | `medium`; requiere Validator y Reviewer independiente |
| RESULT historicos | RESUELTA | existen en `001-010`, pero son artefactos de run subordinados a evidencia ejecutable |
| REVIEW/VALIDATION historicos | RESUELTA | su ausencia no se rellena retroactivamente; se generan solo para revalidacion actual |
| FF-LOCAL-003/006 | RESUELTA | el frontmatter ya figura `Done`; no queda una sincronizacion pendiente para la futura Fase 3 |
| Integridad de ADR | DERIVADA | `FF-LOCALvNext-001-adr-integrity` permanece bloqueada hasta completar correctamente la Fase 3 |
| Findings Tecnotron | AISLADA | registrar solo en `TECNOTRON_REVIEW.md`; no editar estados internos de Tecnotron desde FitFlow |

## Precondiciones para ejecutar Fase 3

| Gate | Owner | Estado actual | Evidencia o condicion |
| --- | --- | --- | --- |
| G1 branch/worktree/baseline | Lifecycle | PASS al recrear | `feat/FF-NEXT-000` en worktree propio, base `046fa1f` |
| G2 TASK/risk/ownership del run preparatorio | Lifecycle + Developer | DEFINIDO | `.ai/tasks/FF-LOCALvNext-000/TASK.md` |
| G3 ownership y allowed write scope de `FF-LOCAL-001..010` | Lifecycle | PENDING | materializar y bloquear rutas antes de la futura Fase 3 |
| G4 correccion documental aceptada | Developer | PENDING | aceptar este diff; no se infiere de validation/review |
| G5 worktree limpio al iniciar Fase 3 | Lifecycle | PENDING | repetir controles Git despues de aceptar/integrar este ciclo |
| G6 entorno para validaciones DB | Developer + Validator | NOT_RUN | no tocar `.env`; una dependencia no disponible se reporta `UNAVAILABLE` |
| G7 Reviewer y Validator independientes | Lifecycle | DEFINIDO | ejecutar ambos gates en el run de Fase 3 |

No ejecutar la Fase 3 mientras G3, G4 o G5 permanezcan pendientes.

## Ejecucion futura de Fase 3

| Paso | Accion | Responsable | Evidencia esperada |
| --- | --- | --- | --- |
| 1 | verificar TASK, branch, worktree, baseline, write scope y limpieza | Lifecycle | registro Git reproducible |
| 2 | inventariar evidencia existente de `FF-LOCAL-001..010` sin inferir archivos ausentes | Agente ejecutor | tabla por task |
| 3 | contrastar criterios contra codigo/tests/migraciones/configuracion y evidencia previa | Agente ejecutor | referencias `ruta:linea` |
| 4 | ejecutar validaciones disponibles | Validator | `VALIDATION.md` actual por task y consolidado |
| 5 | revisar semanticamente la reconciliacion | Reviewer | `REVIEW.md` independiente por task y consolidado |
| 6 | consolidar veredictos | Agente ejecutor | `RESULT.md` global, sin reescribir historia silenciosamente |
| 7 | dejar el run en `PENDING_ACCEPTANCE` | Lifecycle | aceptacion pendiente del Developer |

La tabla global conserva los criterios: codigo verificado, tests, migraciones,
configuracion, evidencia historica, revalidacion actual, estado documental y
veredicto de task.

## Prohibiciones

- no ejecutar Fase 3 en este ciclo;
- no implementar producto ni modificar backend/frontend;
- no editar `.env`, secretos, DB o migraciones;
- no hacer merge, push, reset, eliminar ramas o borrar worktrees;
- no promover estados automaticamente;
- no modificar ADR o documentacion canonica sin DocImpact y aceptacion;
- no inventar evidencia historica;
- no copiar arquitectura, contratos internos o estado de Tecnotron;
- no instalar ni actualizar dependencias.

## Entregable de la futura Fase 3

El run produce `REVIEW.md`, `VALIDATION.md` y `RESULT.md` globales bajo
`.ai/tasks/FF-LOCALvNext-000/`, mas evidencia actual por task cuando aplique.
El resultado global usa un unico veredicto:

- `SPRINT_READY`;
- `CURATION_PARTIALLY_COMPLETED`;
- `DEVELOPER_DECISION_REQUIRED`;
- `WORKTREE_BLOCKED`.

Ninguno de esos veredictos promueve una task a `DONE` sin aceptacion Developer.
