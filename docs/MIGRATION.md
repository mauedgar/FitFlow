---
document_id: FF-MIGRATION-005
status: canonical
machine_context: true
version: 5.1
updated: 2026-08-21
---

# Migracion de baseline v4 a vNext

## Objetivo

Reemplazar la arquitectura centrada en Codebase y un pipeline de indexacion
temprano por una AI Core modular, Workflow-as-Code TypeScript, contexto
determinista y control final del desarrollador.

## Matriz de decisiones

| v4 | vNext | Tratamiento |
| --- | --- | --- |
| Codebase como orquestador | OpenCode detras de `AgentRuntimePort` | v4 superseded; adapter pendiente |
| Jira como tracker | un GitHub Project + Issues + PR + Actions | reemplazo aceptado; integracion pendiente |
| TASK local principal | Issue principal y TASK espejo; fallback local explicito | migracion compatible |
| `PLAN -> EXPLORE -> EXECUTE -> REVIEW -> VALIDATE` | `PLAN -> ROUTE -> EXPLORE -> EXECUTE -> VALIDATE -> REVIEW -> DOC_SYNC` | orden reemplazado |
| rol ligado a modelo | Role Registry + Model Resolver + Model Registry | prohibir asignaciones rigidas |
| RepoMap/AST custom como base | `repo-packager` determinista + lectura real | pipeline anterior superseded |
| Explorer ejecuta un ritual fijo | Explorer decide necesidad y modo de contexto | reducido/drill-down/ampliado bajo demanda |
| LlamaIndex/Qdrant temprano | retrieval semantico despues de contratos y evals | diferido |
| Phoenix inicial | Workflow Observer local; Braintrust/Phoenix evaluables | ADR 0013 superseded |
| documentacion al cierre | `DocImpact -> Doc Curator -> developer approval` | parte del MVP |
| sin politica FinOps formal | FinOps-as-Code, USD 0 incremental y paid API disabled | nueva politica |
| `human` en contratos v1 | `developer` en contratos v2 | traduccion explicita, no alias silencioso |

## Compatibilidad de artefactos

1. Los schemas v1 permanecen legibles para runs historicos.
2. Todo run nuevo usa `.ai/contracts/v2/`.
3. Un migrador v1 -> v2 debe mapear `human` a `developer`, `Codebase` a
   `opencode` solo cuando la evidencia confirme el runtime, y el estado previo
   `REVIEW` a `REVIEWING` sin alterar el veredicto historico.
4. No se mezclan artefactos v1 y v2 dentro de un mismo `run_id`.
5. `FF-AI-000` a `FF-AI-012` quedan superseded como backlog v4. En particular,
   el trabajo iniciado en `FF-AI-001` no se promueve a vNext.

## Autoridad y persistencia

- GitHub es el plano de control del desarrollador cuando la integracion existe.
- `.ai/runs/<run_id>/` conserva JSON durable de runs aceptados.
- SQLite y caches viven bajo `.ai/local/` y son regenerables.
- GitHub comments/checks resumen; no sustituyen el JSON local.
- OpenSpec modela especificaciones funcionales, no TASK ni workflow.

## Gates antes de implementar

1. Verificar versiones y smoke tests sin instalar dependencias.
2. Congelar schemas, registries y Project Profile v2.
3. `repo-packager` fue reparado e integrado en FitFlow-ai mediante PR #2; la
   conformance ContextPackager v2 permanece pendiente en `FF-AI-VNEXT-006`.
4. Implementar State Machine y persistencia antes de roles LLM activos.
5. Medir Router, Explorer y Agent MVP antes de embeddings, MCP o Temporal.
