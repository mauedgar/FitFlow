---
artifact: TASK
schema_version: fitflow-task/v2
task_id: FF-AI-VNEXT-002
title: Implementar doctor y baseline de compatibilidad
status: DONE
task_type: tooling
area: ai_tooling
scope: docs_tooling
lane: ai_orchestrated
risk: low
priority: P0
created_at: "2026-08-18T16:00:00-03:00"
author_role: developer
baseline:
  revision: 44952257482192c438cb38f80be623056fce2409
  fingerprint_status: unavailable
  working_tree_fingerprint: null
  fingerprint_reason: "El arbol contiene cambios de la migracion vNext en curso; no se capturo un fingerprint antes de la tarea."
github_issue: null
openspec_change: null
ownership_keys:
  - "path:../FitFlow-ai/scripts/doctor"
required_docs:
  - docs/ai/cli-contract.md
  - ../FitFlow-ai/docs/compatibility-baseline.md
  - ../FitFlow-ai/docs/implementation-roadmap.md
---

# Objetivo

Implementar `ffai doctor` como primer comando operativo de AI Core dentro de
`FitFlow-ai`: descubre y reporta version, path, capabilities y salida exacta del
toolchain sin instalar ni actualizar dependencias.

## Scope

- `../FitFlow-ai/scripts/doctor/` (bin, lib, tests);
- reporte JSON v2 en STDOUT y diagnostico en STDERR;
- exit codes segun cli-contract (`0`, `2`, `4`, `10`);
- incorporacion de `FitFlow-ai` al repo de FitFlow en la ubicacion canonica.

## Fuera de scope

- implementar contracts/registries loaders (FF-AI-VNEXT-003);
- State Machine ni Run Store (FF-AI-VNEXT-004);
- installs, upgrades ni cambios de entorno.

## Restricciones

- `doctor` solo descubre y reporta; no instala ni actualiza dependencias;
- stdout JSON, stderr diagnostico;
- funcionar en Windows PowerShell y en CI.

## Criterios de aceptacion

| ID | Criterio | Evidencia esperada |
| --- | --- | --- |
| AC-1 | `node --test` del doctor pasa en Windows | 6/6 tests PASS |
| AC-2 | `ffai doctor` detecta node, npm, python, git, gh, openspec, repomix y opencode | reporte JSON con status AVAILABLE |
| AC-3 | `ffai doctor` reporta repo-packager y project-profile | componentes con status coherente |
| AC-4 | Exit code 0 cuando los requeridos estan disponibles | comando con `$LASTEXITCODE` 0 |
| AC-5 | `FitFlow-ai` esta incorporado al repo de FitFlow | directorio y docs en el arbol |

## Impacto documental

`canonical_update` y actualizacion de `docs/ai/cli-contract.md` y
`docs/current-state.md`.
