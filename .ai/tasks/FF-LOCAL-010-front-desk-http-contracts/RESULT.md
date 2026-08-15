---
id: FF-LOCAL-010
status: Review
area: backend
execution_lane: codex
type: feature
---

# Resultado consolidado

## TASK 010.1 - Front Desk y check-in

- Router reducido a HTTP/DI; la consulta y las transiciones viven en
  `front_desk_service`.
- La vista del dia usa `LOCAL_TZ`, relaciones SQLAlchemy tipadas y no muta
  propiedades hibridas de disponibilidad.
- Se agrego `POST /api/v1/front-desk/sessions/{session_id}/bookings/{booking_id}/check-in`.
- Check-in permite solo `confirmed -> attended`, registra `checked_in_at` y
  conserva Booking.

| Validacion | Estado | Evidencia |
|---|---|---|
| Pyright Front Desk | PASS | 0 errores y 0 warnings. |
| OpenAPI | PASS | 7 rutas Front Desk, incluidos day board y check-in. |
| Integracion dirigida | PASS | 19 passed; check-in persiste asistencia. |

## TASK 010.2 - Contratos HTTP publicos

- Se corrigio el orden de registro de rutas publicas de GymClass, Teacher y
  ClassSchedule para que no sean capturadas por sus rutas UUID.
- `GymClassPublic` recibe ahora todos los campos obligatorios desde la
  proyeccion de service.
- `httpx==0.28.1` integra el perfil de test para habilitar API tests.

| Validacion | Estado | Evidencia |
|---|---|---|
| Pyright de rutas/proyecciones modificadas | PASS | 0 errores y 0 warnings. |
| HTTP catalogo publico GymClass | PASS | `/api/v1/gym-classes/public` devuelve 200 y payload completo. |
| Fixture HTTP async compartido | NOT_RUN | El TestClient exploratorio requiere lifecycle controlado del engine async. |

## Alcance descartado

- La task propuesta para matriz de roles y ciclo JWT/Redis (010.3) queda
  descartada y no se mantiene como plan pendiente de esta feature flag.
- La validacion HTTP integral del MVP queda fuera del cierre actual; se retoma
  unicamente mediante una nueva decision de alcance.

## Cierre

FF-LOCAL-010 queda en `Review` con las dos tareas implementadas arriba. No se
crea una task adicional ni se afirma cobertura HTTP integral no ejecutada.
