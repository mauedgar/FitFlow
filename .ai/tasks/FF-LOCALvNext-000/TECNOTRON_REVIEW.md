# Cuarentena de findings Tecnotron/FitFlow-ai

Este archivo es un informe operativo task-scoped. No es documentacion canonica
de FitFlow, un ADR, un `REVIEW.md` de aceptacion, una fuente de verdad de
Tecnotron ni autorizacion para modificar otro repositorio.

La inspeccion externa fue read-only y acotada a
`C:/Users/maued/orca/workspaces/FitFlow-ai/feat-current-state-2`. Ningun estado
`FF-AI-VNEXT-*` se modifica o declara desde FitFlow.

## Hallazgos aislados

| Hallazgo | Clasificacion | Origen FitFlow | Responsabilidad real | Evidencia | Impacto en FitFlow | Accion recomendada |
| --- | --- | --- | --- | --- | --- | --- |
| El resumen de estado AI Core conserva `005 NEXT`, `006 READY` y adapters pendientes, mientras la fuente externa registra implementaciones y promociones posteriores. | CROSS_REPO_REFERENCE | `docs/current-state.md:33-53`; `docs/roadmap.md:26-32`; `docs/ai/roadmap-vnext.md:9-18` | CROSS_REPO | `FitFlow-ai/docs/current-state.md:13-69` | DOC_IMPACT | En una task cross-repo futura, reducir FitFlow a un snapshot de integracion con baseline o a un puntero; no actualizar estados internos silenciosamente. |
| El backlog local mantiene `005/006 READY` y `007-009 BACKLOG`, aunque se declara espejo `MIGRATION_PENDING`. | CROSS_REPO_REFERENCE | `.ai/backlog/vnext.yaml:1-6,28-54` | CROSS_REPO | `FitFlow-ai/docs/current-state.md:23-69,136-148` | DOC_IMPACT | Definir ownership y sincronizacion del espejo antes de editarlo; conservar Project Profile, TASK y runs especificos de FitFlow. |
| La referencia externa de FitFlow usa un snapshot documental `91a4697`, anterior al worktree autoritativo inspeccionado. | CROSS_REPO_REFERENCE | `docs/SOURCE_OF_TRUTH.md:56-64`; `docs/ai/README.md:15-18`; `docs/ai/roadmap-vnext.md:11-18` | CROSS_REPO | `FitFlow-ai/docs/SOURCE_OF_TRUTH.md:46-68` | DOC_IMPACT | Revalidar paths y baseline en una task de integracion; mantener solo referencias estables y no duplicar el roadmap. |
| Project Profile es propio del producto, pero las afirmaciones sobre resolver/adapters `FF-AI-VNEXT-005` quedaron stale. | CROSS_REPO_REFERENCE | `docs/ai/project-profile-and-openspec.md:13-19,38-42` | CROSS_REPO | `FitFlow-ai/docs/current-state.md:23-24,136-148` | DOC_IMPACT | Conservar el perfil y sus valores en FitFlow; actualizar solo la referencia de integracion cuando exista ownership. |
| ADR 0015 mezcla la decision FitFlow de consumir contexto verificable con estado interno de `repo-packager` y ContextPackager. | CROSS_REPO_REFERENCE | `docs/adr/0015-deterministic-context-packaging.md:18-32` | TECNOTRON | `FitFlow-ai/docs/current-state.md:17-24,120-134` | DOC_IMPACT | En ADR integrity futuro, conservar el contrato de consumo FitFlow y enlazar implementacion/conformance a Tecnotron. |
| ADR 0016 conserva como pendientes adapters de GitHub/OpenSpec asignados a `FF-AI-VNEXT-005`. | CROSS_REPO_REFERENCE | `docs/adr/0016-github-openspec-control-plane.md:26-30` | TECNOTRON | `FitFlow-ai/docs/current-state.md:23-24` | DOC_IMPACT | Reencuadrar el ADR como decision de adopcion de FitFlow; estado de adapters permanece externo. |
| ADR 0014 describe State Machine, Router, Model Resolver y adapter OpenCode como arquitectura interna. | TECNOTRON_OWNED | `docs/adr/0014-ai-core-workflow-opencode-adapter.md:19-32` | TECNOTRON | `FitFlow-ai/docs/operational-architecture.md:96-110,151-163,201-229` | DOC_IMPACT | Mantener en FitFlow solo gates y contrato de integracion necesarios; proponer reencuadre mediante DocImpact, sin editarlo en este ciclo. |
| ADR 0017 combina politica FitFlow (`USD 0`, paid disabled, evidencia durable) con ledger, observer y FinOps genericos. | SHARED_PATTERN | `docs/adr/0017-run-ledger-finops-observer.md:12-25` | TECNOTRON / CROSS_REPO | `FitFlow-ai/docs/operational-architecture.md:214-229`; `FitFlow-ai/docs/current-state.md:25-30` | DOC_IMPACT | Conservar restricciones y evidencia propias del producto; referenciar implementacion generica externa. |
| Documentos superseded de roles, routing, registries, ContextPackager, runtime, FinOps y observability siguen fisicamente en el corpus activo. | TECNOTRON_OWNED | `docs/ai/README.md:20-51`; ejemplo `docs/ai/roles-and-model-routing.md:1-67` | TECNOTRON | `FitFlow-ai/docs/SOURCE_OF_TRUTH.md:32-68` | DOC_IMPACT | Una task documental posterior debe retirar consumers o archivar sin promover esas copias; no expandirlas desde FitFlow. |
| `context-artifacts.md` mezcla wire contracts/runs consumidores de FitFlow con producers y defaults genericos, y ya se marca `MIGRATION_PENDING`. | SHARED_PATTERN | `docs/ai/context-artifacts.md:1-55`; `docs/ai/README.md:27` | CROSS_REPO | `FitFlow-ai/docs/current-state.md:136-148` | DOC_IMPACT | Separar en una task con ownership: FitFlow conserva evidencia/contratos consumidores; Tecnotron conserva producers, defaults e implementacion reusable. |
| Los schemas v2 estan activos en FitFlow, pero la publicacion/ubicacion compartida de contracts sigue pendiente. | UNCLEAR_OWNERSHIP | `.ai/contracts/README.md:1-34`; `docs/process/information-artifacts.md:11-37` | CROSS_REPO | `FitFlow-ai/docs/current-state.md:136-148` | DOC_IMPACT | No copiar ni migrar schemas en este ciclo; resolver contrato compartido y compatibilidad en una task dedicada. |
| La configuracion local contiene valores de roles/models/providers/FinOps que FitFlow necesita, mientras loaders, routing y policy generica pertenecen al core. | SHARED_PATTERN | `.ai/README.md:1-10`; `.ai/config/README.md:1-15` | TECNOTRON / CROSS_REPO | `FitFlow-ai/docs/operational-architecture.md:151-212,231-241` | NONE | Mantener Project Profile y valores especificos en FitFlow; no documentar aqui loaders ni arquitectura interna. |
| El lifecycle general es reusable, pero su engine, provider updates, adapters y automatizacion Git/GitHub no son arquitectura de producto. | SHARED_PATTERN | `docs/process/task-lifecycle-and-reporting.md:9-87`; `docs/MIGRATION.md:17-32` | TECNOTRON | `FitFlow-ai/docs/task-lifecycle.md:14-28,78-128,242-266` | DOC_IMPACT | FitFlow adopta branch/worktree, roles separados, validacion, acceptance gate y evidencia; expresa reglas de producto sin copiar engine o adapters. |
| `docs/MIGRATION.md` conserva una migracion detallada de AI Core y claims de implementacion ya superados. | TECNOTRON_OWNED | `docs/MIGRATION.md:9-32,53-60` | TECNOTRON | `FitFlow-ai/docs/current-state.md:13-69` | DOC_IMPACT | Mantenerlo sin cambios hasta una task con ownership que reduzca FitFlow a compatibilidad e integracion del producto. |
| La plataforma Orca/OpenCode se menciona en FitFlow para explicar aislamiento y runtime, pero su implementacion no pertenece al producto. | CROSS_REPO_REFERENCE | `docs/current-state.md:44-48`; `docs/SOURCE_OF_TRUTH.md:42-46` | TECNOTRON / CROSS_REPO | `FitFlow-ai/docs/operational-architecture.md:112-163` | NONE | Conservar solo la frontera minima: Git worktree aisla escritura y el runtime es reemplazable. |

## Frontera confirmada

- `FITFLOW_OWNED`: producto, Sprint 6.8, `FF-LOCAL-*`, Project Profile,
  configuracion especifica, tasks/runs del producto y ADR de adopcion.
- `TECNOTRON_OWNED`: Agent Runtime, Router, Model Resolver, FinOps generico,
  ContextPackager, registries/loaders, orchestration, adapters y engine del
  lifecycle reusable.
- `SHARED_PATTERN`: task branch, worktree task-scoped, baseline, roles
  separados, validacion normalizada, acceptance gate, integracion verificada,
  evidencia durable y cleanup seguro.

## Resultado de cuarentena

Los findings son no bloqueantes para corregir los planes task-scoped. Si una
referencia cross-repo afecta la futura Fase 3, se usa como aviso de freshness y
no como autoridad sobre el estado del producto. Toda correccion canonica queda
para DocImpact y una task posterior con ownership explicito.
