---
document_id: FF-AI-OPENCODE-001
status: superseded
machine_context: false
version: 2.0
updated: 2026-08-18
superseded_by: FitFlow-ai/docs/development-pipeline-adapter.md
---

# Contrato del adapter OpenCode

## Frontera

OpenCode CLI/headless es la superficie operativa primaria. Desktop queda como
interfaz manual del desarrollador y no forma parte del contrato automatizado.
AI Core depende de `AgentRuntimePort`; configuracion, permisos y nombres propios
de OpenCode no se filtran a los contratos de dominio del workflow.

## Responsabilidades

1. Detectar version y capacidades reales.
2. Mapear roles, skills, modelos y permisos desde registries v2.
3. Restringir tools y paths por rol.
4. Validar input/output contra schemas v2.
5. Registrar runtime ID, provider, pool, tokens y errores.
6. Respetar abort, timeout, retries y high-risk block.

La implementacion puede usar `opencode run --format json` o adjuntarse a una
instancia local de `opencode serve`. No automatiza la UI Desktop.

## Conformance gates

- no puede emitir `DONE`;
- no puede instalar dependencias, hacer commit/push/merge ni escribir fuera de
  ownership;
- rechaza output invalido o modelo no elegible;
- conserva actor `developer` en gates y decisiones;
- permite reviewer independiente;
- no convierte una sesion de chat en fuente de verdad.

## Estado verificado

La CLI `opencode 1.18.18` esta disponible. Discovery enumero modelos LM Studio
con runtime IDs concretos; el smoke de inferencia y la conformance suite del
adapter permanecen pending.

GitHub Copilot queda deferred. No existe acceso programatico autorizado: si se
usa, el desarrollador actua como intermediario y transmite la orden fuera de
AI Core. Copilot no pertenece a los pools elegibles del Model Resolver.
