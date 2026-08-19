---
document_id: FF-AI-CLI-001
status: planned
machine_context: true
version: 2.0
updated: 2026-08-18
---

# Contrato CLI previsto

La entrada unica de AI Core sera `ffai`. `ffai doctor` esta implementado como
probe de compatibilidad en `../FitFlow-ai/scripts/doctor/`; el resto de comandos
permanece planned.

```text
ffai doctor
ffai run --task <id>
ffai context reduced --task <id> --query <text>
ffai context drill-down --task <id> --path <path>
ffai context expanded --task <id> --path <path> [--path <path>]
ffai validate --run <id>
ffai observe [--run <id>]
ffai sync github --task <id>
```

STDOUT emite JSON v2 o una vista solicitada; STDERR es diagnostico. Exit codes:
`0` success, `2` invalid input/schema, `3` blocked, `4` unavailable, `5` stale,
`6` partial y `10` internal error.

`doctor` solo descubre y reporta. No instala ni actualiza dependencias.

Para roles agentic, `ffai` invoca el adapter OpenCode CLI/headless. No controla
OpenCode Desktop ni expone GitHub Copilot como proveedor programatico.
