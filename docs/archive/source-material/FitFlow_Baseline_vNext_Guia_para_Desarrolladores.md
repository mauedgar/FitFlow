---
document_id: FF-ARCHIVE-SOURCE-GUIDE-001
status: historical
machine_context: false
indexing: excluded
updated: 2026-08-19
supersedes: "FitFlow_Baseline_vNext_Guia_para_Desarrolladores.docx (movido a superseded)"
---

# GUÍA PARA DESARROLLADORES

**FitFlow Baseline vNext 5.0**

- **Audiencia:** Desarrolladores de FitFlow y mantenedores de FitFlow-ai
- **Fecha:** 18 de agosto de 2026
- **Autoridad:** Explicativa; los documentos canónicos Markdown gobiernan
- **Fuentes:** Baseline v4 + informes 01, 02, 02.1, 03, 04 y 05

**ESTADO: BASELINE PROPUESTA / ACEPTACIÓN PENDIENTE**

> **Lectura rápida.** vNext no agrega más agentes por sí misma. Separa decisiones, ejecución y evidencia para que cada componente pueda cambiar sin rediseñar el sistema completo.

## 1. Qué cambió

La baseline v4 definía una arquitectura centrada en una superficie de orquestación y adelantaba un pipeline estructural y vectorial amplio. vNext conserva la disciplina de contexto verificable, ownership y aceptación del desarrollador, pero reemplaza las piezas que quedaron obsoletas o demasiado acopladas.

| Antes (v4) | Ahora (vNext) | Implicación |
| --- | --- | --- |
| Codebase gobierna la orquestación | AI Core gobierna; OpenCode es un adapter | El runtime puede reemplazarse |
| Jira como tracker | GitHub Project + Issues + PR + Actions | Un solo plano operativo |
| Rol asociado a modelo | Role Registry + Model Resolver | La capacidad se selecciona por task |
| RepoMap/AST/vectorización temprana | repo-packager determinista; retrieval posterior | Menor complejidad inicial |
| Review antes de validate | Validate antes de Review | Reviewer recibe evidencia ejecutada |
| Aceptación humana | Aceptación del desarrollador | Terminología y enum v2 coherentes |

## 2. Cómo se divide el sistema

FitFlow y FitFlow-ai forman una célula, pero no comparten responsabilidades. La separación permite reutilizar AI Core en otro proyecto sin mover la doctrina del producto.

| Superficie | Posee | No posee |
| --- | --- | --- |
| FitFlow | Código de producto, docs canónicos, Project Profile, contracts y runs | Implementación genérica de AI Core |
| FitFlow-ai | Workflow genérico, ports, policies, adapters y observer | Reglas de Booking/RRULE o autoridad documental |
| OpenCode | Sesiones, modelos y tools detrás del adapter | State Machine, gates o DONE |
| GitHub | Control operativo y visualización | La evidencia JSON completa del run |
| OpenSpec | Specs y deltas funcionales | TASK, workflow, review o ADR |

## 3. Flujo de una task

```text
Developer Planner
  -> ROUTING
  -> EXPLORING
  -> EXECUTING
  -> VALIDATING
  -> REVIEWING
  -> DOC_SYNC
  -> PENDING_ACCEPTANCE
  -> Developer: DONE
```

1. El desarrollador define objetivo, scope, riesgo, ownership, criterios y baseline.
2. Router aplica reglas deterministas; usa una LLM económica solo si la ruta sigue siendo ambigua.
3. Explorer decide qué evidencia necesita el siguiente rol y formula un ContextRequest.
4. repo-packager ejecuta el modo solicitado y devuelve contenido, metadata y omissions.
5. Model Resolver selecciona un recurso elegible después de conocer rol, riesgo y contexto.
6. Coder implementa dentro del ownership; Validator ejecuta gates deterministas.
7. Reviewer inspecciona diff, fuente real y ValidationResult; un FAIL vuelve a Router.
8. Doc Curator propone cambios durables; el desarrollador acepta, integra y marca DONE.

## 4. Roles y autoridad

| Rol | Estado | Responsabilidad principal |
| --- | --- | --- |
| Developer Planner | Activo | Plan, riesgo, decisiones y aceptación |
| Router | Especificación activa | Seleccionar rol/capacidad o escalar |
| Model Resolver | Especificación activa | Elegir pool y runtime elegibles |
| Explorer | Especificación activa | Determinar evidencia mínima |
| Coder B / A | Especificación activa | Implementación low/medium |
| Coder Strong A / Architect | Especificación condicional | Escalamiento autorizado |
| Reviewer | Especificación activa | Findings y veredicto independiente |
| Doc Curator | Especificación activa | Proponer sincronización documental |
| Validator | Especificación no agentic | Ejecutar y clasificar gates |

> **Regla de autoridad.** El modelo más capaz no obtiene más autoridad. Role Registry define autoridad; Model Registry solo permite encontrar quién puede ejecutar el rol.

## 5. Contexto sin ritual fijo

Explorer puede solicitar cualquier modo directamente. El objetivo es entregar el menor contexto suficiente, no obligar a pasar por tres rondas.

| Modo | Qué entrega | Cuándo usar |
| --- | --- | --- |
| reduced | PageRank, firmas, candidatos, scores y tokens | Overview |
| drill-down | Mapa focalizado de una zona | Comprender un módulo |
| expanded | Código real de paths explícitos | Implementar o revisar |

- repo-packager no explora, no decide suficiencia y no recuerda qué vio un modelo.
- Un pedido que excede límites devuelve PARTIAL/omitted paths; nunca se trunca en silencio.
- Tests se incluyen por perfil de consumidor, no por una exclusión universal.
- Coder y Reviewer deben abrir la fuente real antes de modificar o aprobar.
- Los bundles stale se rechazan; Run State conserva lineage y expansiones.

## 6. Artefactos y autoridad

Los contracts v2 son el lenguaje estable entre AI Core y sus adapters. Los Markdown son vistas legibles; los JSON del run son evidencia durable.

```text
.ai/runs/<run_id>/
  run-state.json
  events.jsonl
  route.json
  context-*.json
  execution.json
  validation.json
  review.json
  doc-impact.json
  usage.jsonl
  result.json
```

- GitHub Issue es la TASK principal cuando existe sincronización; TASK.md es espejo local.
- better-sqlite3 implementará el checkpoint/proyección local reconstruible.
- PR comments, checks y Actions artifacts son visualización o transporte.
- OpenSpec describe el cambio funcional; no reemplaza la evidencia del run.

## 7. Modelos y FinOps

La selección optimiza el costo del resultado aceptado. Primero se cumplen riesgo, privacidad y calidad; después se elige el recurso suficiente de menor costo total esperado.

```text
deterministic -> local -> included/quota -> free external -> cloud included -> developer
paid API: disabled
```

- Presupuesto incremental: USD 0.
- FastContext es candidato de modelo para Explorer, no implementación obligatoria del rol.
- Los runtime IDs de LM Studio fueron descubiertos en OpenCode; siguen sin benchmark ni conformance.
- GitHub Copilot queda diferido y solo puede intervenir mediante una orden manual del desarrollador.
- Free/experimental tiene criticality ceiling bajo y no aprueba arquitectura o review final.
- Se registran tokens, contexto, latencia, intentos, escalamiento y retrabajo.

## 8. Qué está implementado realmente

| Capacidad | Estado verificado | Siguiente gate |
| --- | --- | --- |
| Baseline vNext | Definida en docs/config/contracts | Aceptación del desarrollador |
| Repomix 1.18.0 | Disponible | Mantener versión |
| repo-packager | Ejecuta con gaps | FF-AI-VNEXT-006 |
| OpenCode CLI | 1.18.18; modelos locales descubiertos | Smoke + conformance |
| OpenCode Desktop | Interfaz manual | Fuera del adapter automatizado |
| OpenSpec / gh | 1.9.0 / 2.97.0; gh autenticado | Bootstrap + adapters |
| GitHub Copilot | Diferido; intermediado por desarrollador | Sin acceso programático |
| AI Core / State Machine / better-sqlite3 | No implementado | Tasks 003-004 |
| Agent MVP | No implementado | Tasks 008-009 |
| Retrieval / MCP / Temporal | Planned/future | Gates posteriores |

## 9. Secuencia recomendada

1. Doctor y compatibilidad sin instalar dependencias.
2. Contracts Zod/JSON Schema y loaders de registries.
3. State Machine, events JSONL y SQLite projection.
4. Project Profile y adapters GitHub/OpenSpec.
5. ContextPackager v2 y correcciones de repo-packager.
6. Router, Model Resolver y FinOps-as-Code.
7. Explorer y conformance del adapter OpenCode.
8. Coder/Validator/Reviewer/Doc Curator como Agent MVP.
9. Fitness functions, Workflow Observer y CI.
10. Retrieval semántico, MCP y Temporal solo tras métricas y gates.

## 10. Checklist para iniciar una task

- Clasificar backend, frontend o mixed.
- Confirmar baseline/fingerprint, risk y ownership keys.
- Usar solo required_docs; excluir source material.
- Registrar Issue o fallback TASK local, nunca dos fuentes editables.
- Solicitar contexto explícito y tratar PARTIAL/STALE como no suficiente.
- Ejecutar Validation antes de Review.
- Producir REVIEW.md, VALIDATION.md y RESULT.md con evidencia.
- Dejar PENDING_ACCEPTANCE; el desarrollador decide DONE.

## 11. Fuentes y trazabilidad

La baseline combina FitFlow Source of Truth v4, el estado real del workspace y los seis informes archivados en docs/archive/source-material/vnext-inputs. Las decisiones finales se materializan en AGENTS.md, docs/SOURCE_OF_TRUTH.md, docs/ai, ADR 0014-0017, .ai/config y .ai/contracts/v2.

- 01 - Informe_Arquitectura_Desarrollo_IA_FitFlow.docx
- 02 - Anexo 1— Estado operativo y evaluación de patrones agentic TypeScript.docx
- 02.1 - Anexo 2 de validación del sistema de asistencia IA.docx
- 03 - Informe_Arquitectura_Propuesta_Sistema_Asistencia_IA_vNext.docx
- 04 - Informe_Herramientas_Skills_Capability_Mapping_vNext.docx
- 05 - Anexo_FinOps_as_Code_AI_Tooling_vNext.docx