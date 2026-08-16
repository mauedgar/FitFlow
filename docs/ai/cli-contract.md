---
document_id: FF-AI-CLI-001
status: planned
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Contrato de CLI previsto

Nombre lógico: `ffai`. La implementación puede usar Node para discovery,
Repomix y serialización; Python `env_tools` aloja Repomix/repo-packager y LlamaIndex.

| Comando | Salida |
| --- | --- |
| `ffai structure dirs --scope backend` | inventario activo backend |
| `ffai structure dirs --scope frontend` | inventario activo frontend |
| `ffai structure dirs --scope total` | inventario activo total |
| `ffai structure classes --scope total` | XML fechado |
| `ffai snapshot --scope backend --task <ID>` | bundle Repomix + manifest |
| `ffai context backend --task <ID> --question <q>` | Context Package backend |
| `ffai context frontend --task <ID> --question <q>` | Context Package frontend |
| `ffai context mixed --task <ID> --question <q>` | Context Package mixto |
| `ffai index build --scope <scope>` | índice de trabajo completo |
| `ffai index sync --dirty <manifest>` | upserts/deletes incrementales |
| `ffai index promote --run <RUN>` | baseline aceptado |
| `ffai query --scope <scope> --task <ID> --text <q>` | primitive de recuperación |
| `ffai verify --run <RUN>` | INDEX_RUN con checks |

## Exit codes

- `0`: éxito y schema válido.
- `2`: input/config inválido.
- `3`: artefacto stale.
- `4`: dependencia unavailable.
- `5`: fallo de parsing/ingesta/validación.
- `6`: operación bloqueada por política.

## Salida

STDOUT contiene solo el JSON/XML principal. Diagnóstico va a STDERR. Los
comandos no instalan dependencias, no acceden a secretos y no escriben fuera de
las rutas configuradas.

Este archivo es especificación; `FF-AI-001–003` deben implementarla y probarla.
