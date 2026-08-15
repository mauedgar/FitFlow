---
id: FF-LOCAL-009
title: Integridad operativa y preservacion historica
status: Review
priority: High
area: backend
execution_lane: codex
type: feature
depends_on: [FF-LOCAL-005, FF-LOCAL-007, FF-LOCAL-008]
---

# Objetivo

Cerrar las invariantes operativas de Booking, sustituir bajas destructivas por
transiciones conservativas y registrar auditoria minima en ClassSchedule.

# Tasks internas

1. Resolver Booking por session o schedule, cancelar con marca temporal y
   preservar capacidad e historia.
2. Eliminar rutas HTTP alcanzables que puedan borrar historia y uniformar las
   bajas como desactivacion, cancelacion o soft delete.
3. Agregar autor de creacion y ultima modificacion a ClassSchedule, sin
   introducir RBAC granular ni una auditoria universal.

# Restricciones

- No modificar cascades ORM ni reglas FK `ON DELETE` existentes.
- Membership permanece 1:1 durante Sprint 6.8.
- No ejecutar migraciones fuera de `fitflow_test`.
- No usar ni afectar recursos Docker de desarrollo ni realizar commits.

# Evidencia requerida

- tests de Booking, baja conservativa y actor audit;
- revision Alembic sin drift accidental de FK;
- documentacion de dominio, estado y ADR actualizada con hechos comprobados.
