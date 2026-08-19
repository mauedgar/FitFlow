---
document_id: FF-AI-SYSTEM-001
status: canonical
machine_context: true
version: 2.0
updated: 2026-08-18
---

# Vision del sistema

## Proposito

Transformar una TASK aprobada en un cambio validado, revisado y documentado,
con contexto minimo, costos medidos y aceptacion del desarrollador.

## Flujo nominal

```text
Developer Planner
  -> GitHub Issue / TASK mirror
  -> Router (deterministic-first)
  -> Explorer
  -> ContextPackager (repo-packager)
  -> Model Resolver
  -> Coder
  -> Validator
  -> Review Context Builder
  -> Reviewer
  -> DocImpact / Doc Curator
  -> Developer Approval
```

OpenCode ejecuta roles mediante un adapter. TypeScript conserva la State
Machine. Ninguna LLM controla libremente transiciones, retries o gates.

## Componentes

| Componente | Responsabilidad | Estado |
| --- | --- | --- |
| AI Core | workflow, policies, ports y contratos | accepted_pending_implementation |
| Project Profile | reglas y paths especificos de FitFlow | baseline v2 definido |
| OpenCode CLI adapter | sesiones, modelos, tools y permisos | CLI disponible; pending conformance |
| GitHub adapter | Issue/PR/Project/Actions | pending; `gh` unavailable |
| OpenSpec adapter | specs y deltas funcionales | pending; CLI unavailable |
| repo-packager | empaquetado determinista | funcional con gaps conocidos |
| Run Store | JSON durable + SQLite local | pending implementation |
| Workflow Observer | vista local de runs y FinOps | planned |

## Invariantes

1. El desarrollador es Planner y autoridad final.
2. Role y Model se resuelven por separado.
3. Router usa reglas antes de LLM.
4. Explorer decide contexto; ContextPackager solo ejecuta la solicitud.
5. Validator precede a Reviewer.
6. Reviewer no corrige codigo por defecto; FAIL vuelve a Router.
7. OpenSpec no reemplaza TASK, Run State ni GitHub.
8. El gasto incremental pago esta deshabilitado.
9. Riesgo alto se bloquea.
10. Los outputs derivados nunca sustituyen lectura de fuente real.
