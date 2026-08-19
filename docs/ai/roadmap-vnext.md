---
document_id: FF-AI-ROADMAP-002
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-18
---

# Roadmap vNext

| Orden | Task | Entregable | Estado inicial |
| ---: | --- | --- | --- |
| 0 | `FF-AI-VNEXT-001` | baseline vNext, fuentes y bundle | done |
| 1 | `FF-AI-VNEXT-002` | doctor/compatibilidad y bootstrap sin installs | pending acceptance |
| 2 | `FF-AI-VNEXT-003` | contracts Zod/JSON Schema y registries loaders | pending acceptance |
| 3 | `FF-AI-VNEXT-004` | State Machine, JSON events, SQLite projection | pending acceptance |
| 4 | `FF-AI-VNEXT-005` | Project Profile, GitHub y OpenSpec adapters | backlog |
| 5 | `FF-AI-VNEXT-006` | ContextPackager v2 y correcciones repo-packager | paused (defer) |
| 6 | `FF-AI-VNEXT-007` | Router, Model Resolver y FinOps policy | backlog |
| 7 | `FF-AI-VNEXT-008` | Explorer + AgentRuntime/OpenCode conformance | backlog |
| 8 | `FF-AI-VNEXT-009` | Coder/Validator/Reviewer/Doc Curator MVP | backlog |
| 9 | `FF-AI-VNEXT-010` | fitness functions, Observer y CI gates | backlog |
| 10 | `FF-AI-VNEXT-011` | semantic retrieval + golden eval | planned |
| 11 | `FF-AI-VNEXT-012` | MCP read-only pilot | planned |
| 12 | `FF-AI-VNEXT-013` | Temporal/orchestrator-workers evaluation | future |

No comenzar una task si su dependencia no tiene evidencia aceptada. Ninguna
fase instala dependencias como efecto lateral de discovery.

## Pausas activas

- `FF-AI-VNEXT-006` (ContextPackager) esta pausado por decision del
  desarrollador desde 2026-08-18.
- `FF-AI-VNEXT-008` queda desacoplado de `006`: usara `repo-packager` actual
  con gaps documentados y difiere la conformance ContextPackager v2 a `006`.
- Si `006` se reactiva, revisar su gate y su impacto sobre `008/009` antes de
  continuar.

## Nota de progreso (2026-08-18)

- `001` aceptado (`BASELINE_ACCEPTED`); `002/003/004` con evidencia y en
  `PENDING_ACCEPTANCE` (tests 24/24 PASS en `../FitFlow-ai`).
- Nucleo minimo operativo alcanzado: contracts v2 (Zod), registries loaders,
  State Machine gobernada por `orchestrator.yaml` y Run Store durable +
  proyeccion SQLite.
- Decisiones abiertas del desarrollador: autorizar install-script de
  `better-sqlite3` para CI, y aceptar nucleo para iniciar `005/007`.

## Decision: carpetas separadas (2026-08-18)

- `FitFlow-ai` NO se incorpora al repo de FitFlow: vive como carpeta hermana en
  `../FitFlow-ai/` con repo propio en preparacion. Se revirtio la copia interna
  y se restauro el README/AGENTS originales de la hermana.
- El codigo de AI Core (doctor, contracts, registries, state machine, run store)
  se movio a `../FitFlow-ai/`; las rutas internas apuntan a `../FitFlow/.ai/`.
- Las referencias en docs, backlog y artefactos de run usan `../FitFlow-ai/...`.
