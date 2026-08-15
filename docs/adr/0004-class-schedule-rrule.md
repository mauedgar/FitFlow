# ADR 0004: RRULE como fuente unica de recurrencia de ClassSchedule

- **Estado:** Implemented
- **Fecha:** 2026-08-12

## Contexto

Mantener dos representaciones de recurrencia crea riesgo de divergencia, fallbacks ambiguos y reglas duplicadas para la generacion de `ClassSession`.

Documentacion anterior trato RRULE como si ya estuviera cerrado; el estado actual no lo confirma y debe verificarse durante Sprint 6.8.

## Decision

`ClassSchedule` usa **RRULE como única fuente de recurrencia**. El valor es una
única línea RFC 5545 con prefijo `RRULE:` y sin `DTSTART`; `start_date` y
`start_time` son el ancla local en `LOCAL_TZ`. La migración convierte y elimina
`days_of_week`.

La creación o actualización de un schedule completa solo ocurrencias futuras
faltantes dentro de 15 días. No modifica ni elimina sesiones existentes,
Bookings ni `capacity_snapshot`; una sesión obsoleta se cancela explícitamente.

## Responsabilidades

- Schema: formato/validacion estructural del dato.
- Service: resolver RRULE, ventana, ocurrencias y conflictos.
- Model/DB: persistir el contrato aprobado.
- Tests: cubrir recurrencia, limites de fecha, conflictos y generacion de sesiones.

## Consecuencias

- reduce ambiguedad;
- requiere completar/verificar implementacion antes de marcar el ADR como Implemented;
- cualquier legacy se elimina con pruebas, no solo para satisfacer documentacion.
