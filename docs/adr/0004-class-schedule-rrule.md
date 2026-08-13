# ADR 0004: RRULE como fuente unica de recurrencia de ClassSchedule

- **Estado:** Accepted / Pending Implementation
- **Fecha:** 2026-08-12

## Contexto

Mantener dos representaciones de recurrencia crea riesgo de divergencia, fallbacks ambiguos y reglas duplicadas para la generacion de `ClassSession`.

Documentacion anterior trato RRULE como si ya estuviera cerrado; el estado actual no lo confirma y debe verificarse durante Sprint 6.8.

## Decision

El target de `ClassSchedule` usa **RRULE como unica fuente de recurrencia**. No se conservara un segundo mecanismo equivalente como verdad paralela una vez completada la migracion.

## Responsabilidades

- Schema: formato/validacion estructural del dato.
- Service: resolver RRULE, ventana, ocurrencias y conflictos.
- Model/DB: persistir el contrato aprobado.
- Tests: cubrir recurrencia, limites de fecha, conflictos y generacion de sesiones.

## Consecuencias

- reduce ambiguedad;
- requiere completar/verificar implementacion antes de marcar el ADR como Implemented;
- cualquier legacy se elimina con pruebas, no solo para satisfacer documentacion.
