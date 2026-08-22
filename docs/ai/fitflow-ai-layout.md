---
document_id: FF-AI-LAYOUT-001
status: superseded
machine_context: false
version: 2.0
updated: 2026-08-18
superseded_by: FitFlow-ai/docs/architecture.md
---

# Layout objetivo de FitFlow-ai

```text
FitFlow-ai/
  src/
    core/                 # functional core, state machine, policies
    contracts/            # Zod y neutral JSON serialization
    registries/           # loaders y validators
    ports/                # interfaces estables
    adapters/             # OpenCode, GitHub, OpenSpec, filesystem, SQLite
    workflows/            # development, bugfix, documentation-sync
    observer/             # vista local y reportes
  tests/
    unit/
    contract/
    integration/
    evals/
  storage/                # ignored; SQLite/caches
  exports/                # ignored; bundles/reportes
  logs/                   # ignored
  docs/
```

FitFlow conserva `AGENTS.md`, `.agents/skills`, `.ai/config`, contratos del
proyecto y artefactos de task/run. Esta distribucion es deliberada: AI Core es
reusable y Project Profile permanece junto al producto cuya doctrina gobierna.

No se crea implementacion ni dependencia al adoptar este layout documental.
