---
id: FF-LOCAL-008
title: Normalizar contratos Pydantic y configurar Redis
status: Done
priority: High
area: backend
execution_lane: codex
type: refactor
depends_on: [FF-LOCAL-007]
---

# Objetivo

Eliminar nombres ambiguos de schemas Pydantic y habilitar Redis aislado para
desarrollo y pruebas, sin cambiar payloads públicos ni activar RBAC draft.

# Scope

- schemas, consumidores y OpenAPI;
- Redis de aplicación y Compose;
- pruebas y documentación.

# Restricciones

- `Role` y `Permission` permanecen drafts;
- no tocar `.env`, recursos Docker de desarrollo ni commits Git;
- Redis de tests no publica puertos ni conserva volumen.
