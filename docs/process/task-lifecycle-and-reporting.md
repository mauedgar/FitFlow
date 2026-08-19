---
document_id: FF-PROCESS-LIFECYCLE-001
status: canonical
machine_context: true
version: 3.0
updated: 2026-08-18
---

# Ciclo de tareas y reportes

## Separacion de responsabilidades

| Sistema | Conserva |
| --- | --- |
| GitHub Project | prioridad y macroestado operativo |
| GitHub Issue | TASK principal cuando esta sincronizada |
| TASK local | espejo validable y fallback offline autorizado |
| OpenSpec | especificacion/delta funcional, no workflow |
| Run State | microestado, rutas, retries y gates |
| artefactos de run | decisiones y evidencia estructurada |
| Git/PR/Actions | diff, discusion, checks e integracion |
| docs/ADR | conocimiento durable aceptado |

## Estados internos

```text
BACKLOG -> READY -> PLANNING -> ROUTING -> EXPLORING -> EXECUTING
        -> VALIDATING -> REVIEWING -> DOC_SYNC -> PENDING_ACCEPTANCE
        -> DONE
```

Estados laterales: `WAITING_DEVELOPER`, `BLOCKED`, `BLOCKED_HIGH_RISK` y
`CANCELLED`.

Rutas de retorno:

- evidencia insuficiente: `EXPLORING`;
- implementacion o validacion fallida: `ROUTING`;
- review fallido localizado: `ROUTING`;
- scope, plan o doctrina invalidos: `PLANNING`;
- decision requerida: `WAITING_DEVELOPER`;
- solo el desarrollador: `PENDING_ACCEPTANCE -> DONE`.

## Macroestados GitHub

| Project | Estados internos |
| --- | --- |
| Backlog | `BACKLOG` |
| Todo | `READY`, `PLANNING` |
| In progress | `ROUTING`, `EXPLORING`, `EXECUTING` |
| In review / testing | `VALIDATING`, `REVIEWING`, `DOC_SYNC` |
| Done | `DONE` |

## Lanes v2

- `developer`;
- `ai_orchestrated`;
- `mixed`;
- `undecided`.

`human` es un valor historico v1 y se migra a `developer`. Rol, modelo y pool
efectivos viven en el run, no en el tracker.

## Artefactos

Los TASK se guardan en `.ai/tasks/<task_id>/`. Los artefactos estructurados se
guardan en `.ai/runs/<run_id>/` usando schemas v2. `REVIEW.md`, `VALIDATION.md`
y `RESULT.md` son vistas para el desarrollador y deben conservar comando,
alcance, salida y estado normalizado.

SQLite bajo `.ai/local/` permite checkpoints y consultas locales; no reemplaza
los JSON durables del run.

## Aceptacion

El workflow termina en `PENDING_ACCEPTANCE`. El desarrollador revisa diff,
validacion, review, riesgo y `DocImpact`, integra mediante Git y promueve a
`DONE`.
