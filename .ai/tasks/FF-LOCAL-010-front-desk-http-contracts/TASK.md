---
id: FF-LOCAL-010
title: Front Desk y contratos HTTP del MVP
status: Done
priority: High
area: backend
execution_lane: codex
type: feature
depends_on: [FF-LOCAL-009]
---

# Objetivo

Consolidar Front Desk sobre el dominio existente y corregir contratos HTTP
publicos sin crear modelos paralelos ni activar RBAC granular.

# Tasks internas implementadas

1. Delegar operaciones de Front Desk a un service tipado y agregar check-in.
2. Alinear rutas publicas, filtros y proyecciones del catalogo HTTP.

La propuesta posterior de una tercera task para la matriz completa de roles y
el ciclo JWT/Redis queda descartada de este plan y no se incorpora al alcance
consolidado del Sprint 6.8.

# Restricciones

- Roles activos: admin, teacher, client y front_desk.
- No activar Role/Permission ni RBAC granular.
- No cambiar frontend salvo un contrato imprescindible validado.
- Tests de base exclusivamente sobre `fitflow_test`.
