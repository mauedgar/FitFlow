---
document_id: FF-AI-CORE-001
status: superseded
machine_context: false
version: 1.0
updated: 2026-08-18
superseded_by: FitFlow-ai/docs/architecture.md
---

# Arquitectura de AI Core

## Frontera

AI Core es tooling reutilizable en `FitFlow-ai`. FitFlow aporta un Project
Profile versionado y conserva la doctrina del producto. AI Core no importa el
runtime de backend o frontend.

## Principios

- functional core / imperative shell;
- Workflow-as-Code TypeScript;
- contratos Zod en AI Core, JSON Schema en bordes y Pydantic cuando un adapter
  Python lo requiera;
- policies y registries como datos versionados;
- adapters reemplazables;
- idempotencia, lineage de contexto y ledger append-only;
- feature flags para toda capacidad posterior al MVP.

## Puertos estables

| Puerto | Responsabilidad |
| --- | --- |
| `AgentRuntimePort` | ejecutar un rol con tools y permisos |
| `TaskStorePort` | leer/sincronizar TASK principal y espejo |
| `SpecStorePort` | consultar cambios funcionales OpenSpec |
| `ContextPackagerPort` | empaquetar una solicitud explicita |
| `RunStorePort` | persistir eventos, estado y artefactos |
| `ValidatorPort` | ejecutar gates deterministas |
| `ReviewPort` | producir review estructurado independiente |
| `DocumentationPort` | proponer cambios por `DocImpact` |
| `QuotaStatePort` | exponer disponibilidad y presion de pools |

## Implementaciones iniciales

OpenCode, GitHub, OpenSpec, repo-packager, SQLite y filesystem son adapters.
Temporal, LlamaIndex, Qdrant, MCP y proveedores adicionales no forman parte del
MVP y solo pueden incorporarse detras de sus puertos.

## Ownership

AI Core posee workflow generico, schemas y adapters. Project Profile posee
paths, comandos, doctrina, labels, riesgos y configuracion de FitFlow. Una
decision especifica de FitFlow no se codifica dentro del core reusable.
