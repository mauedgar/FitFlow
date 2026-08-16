---
document_id: FF-DOMAIN-001
status: canonical
machine_context: true
version: 4.0
updated: 2026-08-16
---

# Dominio de FitFlow

## Vocabulario

```text
User -> Person -> Client -> Membership
              -> Teacher

GymClass -> ClassSchedule -> ClassSession -> Booking
```

| Concepto | Significado |
| --- | --- |
| User | identidad autenticable |
| Person | identidad civil |
| Client | persona que usa el gimnasio |
| Teacher | persona que imparte clases |
| Membership | relación comercial activa o histórica |
| GymClass | catálogo de actividad |
| ClassSchedule | configuración recurrente |
| ClassSession | ocurrencia concreta |
| Booking | reserva e historial de asistencia |

## Membership y planes

Planes conocidos: `gym_only`, `classes`, `premium`, `personalized`. Estados:
`active`, `expired`, `paused`, `cancelled`.

`MembershipPlan` expresa cobertura contratada; `AllowedPlan` restringe un
schedule. `premium` incluye `gym_only`, `classes` y `premium`; `personalized`
incluye además `personalized`. Existencia y compatibilidad son validaciones
distintas.

## Agenda y sesiones

- `ClassSchedule.rrule` RFC 5545, sin `DTSTART`, es la fuente única.
- `start_date` y `start_time` forman el ancla local; `days_of_week` no es contrato
  activo.
- La generación crea solo faltantes futuros dentro de 15 días.
- Nunca reescribe sesiones, bookings ni `capacity_snapshot` históricos.
- `ClassSession.capacity_snapshot` preserva la capacidad de la ocurrencia.
- Disponibilidad derivada:
  `max(capacity_snapshot - current_bookings_count, 0)`.
- Solo bookings que consumen cupo integran el conteo.

Estados de sesión: `scheduled`, `open`, `closed`, `cancelled`, `completed`.
Solo una sesión futura `scheduled` u `open` acepta reservas nuevas.

## Invariantes de Booking

1. Un cliente no reserva dos veces la misma sesión.
2. No se reserva una sesión inválida por estado o tiempo.
3. Debe existir capacidad.
4. Membership y `allowed_plan` se validan cuando correspondan.
5. Capacidad y creación forman una operación transaccional protegida.
6. Los conflictos conservan semántica para mapear HTTP.
7. Si el contrato admite schedule o session, exactamente un identificador está
   presente; el schema valida forma y el service resuelve el caso de uso.
8. Cancelar conserva historia, deja de consumir cupo y no equivale a borrar.

## Preservación

Client, GymClass, ClassSchedule y ClassSession se desactivan o eliminan de forma
conservativa. Membership cambia de estado. Booking no tiene borrado operativo.

## Front Desk

Front Desk es una vista operacional de entidades existentes. Sus schemas son
contratos; no modelos persistentes paralelos.

## Límite del MVP

El flujo prioritario termina en asistencia y estabilización. Métricas y
facturación avanzada son post-MVP salvo nueva decisión.
