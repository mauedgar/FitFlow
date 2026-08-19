---
document_id: FF-ARCHIVE-SOURCE-DECISIONS-001
status: historical
machine_context: false
indexing: excluded
updated: 2026-08-19
supersedes: "FitFlow_Baseline_vNext_Registro_de_Decisiones.docx (movido a superseded)"
---

# REGISTRO DE DECISIONES

**FitFlow Baseline vNext 5.0**

- **Propósito:** Trazar qué se adopta, difiere, reemplaza o rechaza
- **Fecha de corte:** 18 de agosto de 2026
- **Estado:** Aprobación del desarrollador pendiente
- **Autoridad:** Explicativa; ADR 0014-0017 y docs canónicos gobiernan

**ALCANCE: ARQUITECTURA Y PLAN DE IMPLEMENTACIÓN, NO IMPLEMENTACIÓN FUNCIONAL**

## 1. Resultado ejecutivo

vNext conserva el enfoque context-first de v4, pero mueve la estabilidad a contratos, ports, registries y policies. Las herramientas concretas se convierten en adapters reemplazables. El MVP se reduce a Pipeline + Router + State Machine + contexto determinista + gates del desarrollador.

> **Decisión central.** TypeScript decide qué paso ocurre; una LLM resuelve el trabajo permitido dentro de ese paso.

## 2. Decisiones adoptadas

| ID | Decisión | Estado | Evidencia canónica |
| --- | --- | --- | --- |
| D-01 | AI Core + Project Profile | Adoptada | ADR 0014 / ai-core-architecture |
| D-02 | OpenCode detrás de AgentRuntimePort | Pendiente de conformance | ADR 0014 |
| D-03 | Workflow-as-Code TypeScript | Adoptada | development-pipeline |
| D-04 | Developer Planner activo; PlannerAI disabled | Adoptada | roles.yaml |
| D-05 | Router deterministic-first + LLM fallback | Adoptada | roles/model routing |
| D-06 | Model Resolver separado del Router | Adoptada | models.yaml |
| D-07 | Explorer decide; repo-packager empaqueta | Adoptada con gaps | ADR 0015 |
| D-08 | Validate antes de Review | Adoptada | orchestrator.yaml |
| D-09 | Doc Curator activo sin promoción automática | Adoptada | roles.yaml |
| D-10 | GitHub como plano de control | Pendiente adapter | ADR 0016 |
| D-11 | OpenSpec solo para specs funcionales | Pendiente bootstrap | ADR 0016 |
| D-12 | JSON durable + SQLite projection | Pendiente implementación | ADR 0017 |
| D-13 | FinOps USD 0; paid disabled | Adoptada | finops.yaml |
| D-14 | Workflow Observer local primero | Planned | ADR 0017 |
| D-15 | Copilot diferido; intermediación del desarrollador | Adoptada | models/finops |

## 3. Decisiones reemplazadas

| Elemento v4 | Tratamiento vNext | Sucesor |
| --- | --- | --- |
| Codebase como orquestador | Superseded | ADR 0014 |
| Jira | Removed | GitHub Project/Issues |
| RepoMap/AST custom principal | Superseded | ContextPackager/repo-packager |
| LlamaIndex/Qdrant temprano | Deferred | Task vNext 011 |
| Phoenix inicial obligatorio | Superseded | Observer local |
| Review -> Validate | Superseded | Validate -> Review |
| human enum | Migrated | developer enum v2 |
| FF-AI-000..012 | Superseded backlog | FF-AI-VNEXT-002..013 |

## 4. Contratos estables

Los adapters pueden cambiar sin alterar estos artefactos. La serialización neutral usa JSON Schema; AI Core usará Zod y los bordes Python pueden usar Pydantic.

| Familia | Contratos |
| --- | --- |
| Trabajo | Task, RouteDecision, ExecutionResult, RunResult |
| Contexto | ContextRequest, ContextPackageResult |
| Gates | ValidationResult, ReviewResult, DocImpact |
| Runtime | RunEvent, RunState |
| FinOps | UsageRecord, FinOpsSummary |

## 5. Autoridad y persistencia

1. Código, tests, configuración y migraciones verificadas describen la realidad ejecutable.
2. Docs canónicos y ADR describen intención, fronteras y decisiones aceptadas.
3. GitHub conserva control operativo cuando el adapter existe.
4. Artefactos JSON en .ai/runs conservan decisiones y evidencia del run.
5. repo-packager, Repomix, grafos e índices son contexto derivado.
6. Informes y material para desarrolladores viven en archive/source-material y no entran al contexto automático.

## 6. Compatibilidad v1 → v2

| v1 | v2 | Regla |
| --- | --- | --- |
| author_role: human | author_role: developer | Transformación explícita |
| lane: human | lane: developer | Sin alias runtime |
| PLAN/EXPLORE/EXECUTE | PLANNING/EXPLORING/EXECUTING | Mapeo de estado |
| REVIEW/VALIDATE | VALIDATING/REVIEWING | No reordenar historia v1 |
| baseline_revision + fingerprint | baseline object | Agrupación estructural |
| modelo dentro del rol | UsageRecord + Model Resolver | Desacoplamiento |

> **Invariante de migración.** Un run no mezcla schemas v1 y v2. Los artefactos históricos conservan su semántica y orden original.

## 7. Estado de herramientas

| Herramienta | Estado | Decisión |
| --- | --- | --- |
| Repomix 1.18.0 | Verificada | Adoptada |
| repo-packager | Ejecuta; 5 gaps conocidos | Adoptada con correcciones |
| OpenCode CLI | 1.18.18; IDs locales descubiertos | Adapter pendiente de conformance |
| OpenCode Desktop | Interfaz manual disponible | Fuera del adapter automatizado |
| OpenSpec | 1.9.0; raíz no inicializada | Adoptada pendiente de bootstrap |
| GitHub CLI | 2.97.0; autenticada | Adapter pendiente |
| GitHub Copilot | Sin acceso programático | Diferido; intermediado por desarrollador |
| better-sqlite3 13.0.3 | Smoke PASS fuera de FitFlow-ai | Projection store inicial |
| LlamaIndex/Qdrant | No verificados en vNext | Deferred |
| Braintrust/Phoenix/Promptfoo | No adoptados | Evaluate later |
| Temporal | No adoptado | Post-MVP |

## 8. Gates de implementación

- Doctor reproduce versiones y capabilities sin instalar dependencias.
- Schemas y registries pasan validación y conformance tests.
- State Machine prueba transiciones, idempotencia, retries y developer gate.
- repo-packager corrige UTF-8, .env, globs, .repomixignore, PARTIAL y selección scoped.
- OpenCode adapter prueba permisos, output validation, model ID y high-risk block.
- Router/Model Resolver se evalúan con fixtures y quota state.
- Agent MVP demuestra una task low/medium sin paid API.
- Retrieval, MCP y Temporal requieren gates propios y feature flag.

## 9. Decisiones aún no congeladas

- Runtime IDs efectivos y ranking de modelos por rol.
- Thresholds de Router, budgets y retry limits después de evals.
- Entorno oficial de FitFlow-ai; scripts/.venv_tools no lo define.
- Proveedor de observabilidad externo, si el Observer local resulta insuficiente.
- Embedding, vector store y thresholds de semantic retrieval.
- Temporal y orchestrator-workers después del MVP.

## 10. Trazabilidad de fuentes

Los informes 01 y 02 explican la evolución temprana; el anexo 02.1 valida el estado operativo y GitHub; los informes 03, 04 y 05 refinan la arquitectura final, el capability mapping y FinOps-as-Code. El estado real del workspace corrige toda afirmación no reproducible.

| Fuente | Uso |
| --- | --- |
| Baseline v4 | Doctrina heredada y trazabilidad |
| Informes 01/02/02.1 | Evolución y validaciones del desarrollador |
| Informes 03/04/05 | Arquitectura, tools/skills y FinOps finales |
| Workspace FitFlow/FitFlow-ai | Estado implementado y gaps |
| Docs/ADR vNext | Decisión canónica resultante |