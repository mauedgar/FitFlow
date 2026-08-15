# ADR 0010: Preservacion de historia y auditoria minima de schedules

- **Estado:** Accepted
- **Fecha:** 2026-08-13

## Decision

- Booking se cancela por estado y conserva la fila, incluyendo `cancelled_at`.
- Client, GymClass y ClassSchedule se desactivan o aplican soft delete; no
  desasocian relaciones que puedan activar `delete-orphan`.
- Membership se finaliza mediante `status=cancelled`; sigue siendo 1:1 durante
  Sprint 6.8.
- ClassSession conserva su soft delete administrativo y sus Bookings.
- `ClassSchedule` registra `created_by_id` y `updated_by_id` como referencias
  nullable a User con `ON DELETE SET NULL`.

## Consecuencias

No se modifican las cascades ORM ni las FK existentes. La auditoria de actor se
limita a ClassSchedule; RBAC granular, auditoria universal y Membership 1:N
permanecen fuera de este Sprint.
