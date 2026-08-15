# Dominio de FitFlow

**Estado:** Canonico  
**Actualizado:** 2026-08-13

## 1. Proposito

Mantener un vocabulario estable del negocio y las invariantes que deben sobrevivir a refactors, cambios de framework y herramientas de IA.

## 2. Identidad y relacion comercial

```text
User
  -> Person
      -> Client
      -> Teacher

Client -> Membership
```

- **User:** identidad autenticable.
- **Person:** identidad civil/persona.
- **Client:** rol del dominio asociado al uso del gimnasio.
- **Teacher:** rol profesional que imparte clases.
- **Membership:** relacion comercial activa o historica del cliente.

Planes conocidos: `gym_only`, `classes`, `premium`, `personalized`.  
Estados conocidos: `active`, `expired`, `paused`, `cancelled`.

La existencia de una membership valida y la compatibilidad de esa membership con una clase/agenda son validaciones distintas.

`MembershipPlan` expresa la cobertura contratada por el cliente, mientras que
`AllowedPlan` expresa la restricción de un `ClassSchedule`. Ambos conservan los
valores `gym_only`, `classes`, `premium` y `personalized` cuando corresponde.
Un plan `premium` incluye acceso a horarios `gym_only`, `classes` y `premium`;
un plan `personalized` incluye esos accesos y los horarios `personalized`.

## 3. Dominio operativo

```text
GymClass -> ClassSchedule -> ClassSession -> Booking
```

### GymClass
Catalogo de actividades. Contiene propiedades de referencia como nombre, tipo, dificultad, duracion y capacidad por defecto cuando corresponda.

### ClassSchedule
Configuracion recurrente de una clase; no es una ocurrencia concreta.

**Fuente única:** `rrule` RFC 5545, sin `DTSTART`; `start_date` y `start_time`
definen el ancla local. `days_of_week` fue eliminado.

El schedule puede contener profesor, ventana de vigencia, hora, duracion, capacidad y restricciones como `allowed_plan`.
La generación completa únicamente sesiones futuras faltantes dentro de 15 días;
no modifica snapshots ni historial existente.

### ClassSession
Ocurrencia concreta de un schedule. Debe preservar `capacity_snapshot` para no reescribir historicamente la capacidad de una sesion cuando cambie el schedule.

Disponibilidad conceptual:

```text
available_spots = max(capacity_snapshot - current_bookings_count, 0)
```

`current_bookings_count` contabiliza solamente reservas que consumen cupo;
una reserva con estado `cancelled` permanece como historial pero no ocupa lugar.

La cancelación cambia el estado de la sesión. El endpoint administrativo de
eliminación realiza soft delete (`active=false` y `deleted_at`), por lo que no
borra sus Bookings ni reescribe la historia.

La disponibilidad mostrada puede ser derivada; la operacion critica de reserva debe confiar en una comprobacion transaccional.

Estados operativos conocidos: `scheduled`, `open`, `closed`, `cancelled`, `completed`.

### Booking
Reserva/intencion de asistencia de un cliente a una `ClassSession`.

Estados conocidos: `confirmed`, `cancelled`, `attended`, `no_show`.

Cancelar una reserva conserva historia; no equivale a soft-delete.
Booking no expone borrado operativo: toda baja funcional se representa como
cancelación con estado `cancelled` y, cuando corresponda, `cancelled_at`.

Una sesión `scheduled` u `open` y futura puede aceptar reservas. Una sesión
`closed`, `cancelled`, `completed` o pasada no admite reservas nuevas.

Las bajas de Client, GymClass y ClassSchedule preservan historia por
desactivación o soft delete. Membership se cancela por estado; su cardinalidad
permanece 1:1 durante Sprint 6.8.

## 4. Invariantes de Booking

1. Un cliente no puede reservar dos veces la misma sesion.
2. No se crean reservas sobre sesiones invalidadas por estado o tiempo.
3. Debe existir capacidad.
4. Debe existir una membership compatible cuando la regla de negocio lo requiera.
5. `allowed_plan` se valida en la capa de negocio.
6. Comprobacion de capacidad y creacion deben ser parte de una operacion transaccional protegida.
7. Los errores de conflicto deben conservar semantica suficiente para mapearse a HTTP apropiadamente.
8. Cuando el contrato admita schedule o session, exactamente uno de `class_schedule_id` y `class_session_id` debe estar presente; la regla estructural pertenece al schema y la resolucion pertenece al service.

## 5. Front Desk

Front Desk no crea un dominio paralelo. Consume `ClassSession`, `Booking`, `Client`, `GymClass`, `Teacher` y sus vistas Pydantic para operacion diaria.

Schemas como `FrontDeskSessionView`, `FrontDeskBookingView`, `FrontDeskDayView` o equivalentes deben ser vistas/contratos, no nuevos modelos persistentes duplicados.

## 6. Crecimiento del producto

Direccion vertical preferida:

```text
Identidad
 -> Cliente
 -> Membresia
 -> Clase
 -> Agenda
 -> Sesion
 -> Reserva
 -> Asistencia
 -> Metricas
 -> Facturacion
```

El MVP termina antes de facturacion/pagos avanzados. Nuevos modulos deben justificar su relacion con este flujo.
