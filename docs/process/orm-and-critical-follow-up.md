# Seguimiento posterior al baseline ORM

Estado: propuesto

Baseline de referencia: Roadmap v3 / SQLAlchemy 2.0

Alcance: trabajo deliberadamente postergado y fallas relevantes detectadas durante la auditoría.

## Propósito

Este documento no redefine el dominio ni autoriza cambios de esquema. Ordena el trabajo que debe revisarse después de estabilizar el metadata ORM y la base de pruebas aislada.

## Prioridad 0 — bloqueantes funcionales

### FF-FOLLOW-01 — Eliminar el borrado físico alcanzable desde Client

`DELETE /clients/{client_id}` llama a `unlink_user_profile()`, que asigna `user.person_profile = None`. La relación conserva `cascade="all, delete-orphan"`; por lo tanto, la desasociación puede eliminar físicamente `Person`/`Client` y alcanzar membresías o reservas mediante las cascades existentes.

Política esperada: desactivar Client, conservar Membership y Booking, y mantener el vínculo histórico necesario. No cambiar cascades ORM ni FK `ON DELETE` hasta aprobar una política y un ADR específico.

Criterios mínimos:

- el endpoint no ejecuta eliminación física ni dispara `delete-orphan`;
- la desactivación es transaccional;
- memberships, bookings y sesiones históricas permanecen consultables;
- pruebas de integración demuestran conservación antes y después de la baja.

### FF-FOLLOW-02 — Corregir el contrato HTTP 204 de logout

La importación completa de FastAPI falla al registrar `POST /logout`: FastAPI rechaza un status 204 configurado con una respuesta que puede contener cuerpo.

Criterios mínimos:

- `from app.main import app` funciona con la configuración mínima documentada;
- logout devuelve 204 sin cuerpo o adopta otro status coherente;
- OpenAPI se genera sin assertions.

## Prioridad 1 — integridad e historia

### FF-FOLLOW-03 — Definir políticas de ciclo de vida y cascades

Preservar por ahora las cascades y reglas `ON DELETE` existentes. Crear un ADR que defina explícitamente:

- Booking: cancelación por estado; nunca borrado operativo;
- ClassSession: cancelación/finalización; conservar historia;
- ClassSchedule y GymClass: desactivación; conservar sesiones generadas;
- Client y User: desactivación; evaluar anonimización;
- Membership: finalización/cancelación e historial.

Después del ADR, diseñar migraciones forward-only y pruebas de conservación. Alembic no debe proponer cambios de FK mientras la política siga pendiente.

### FF-FOLLOW-04 — Sustituir DELETE de ClassSession por transición de estado

`DELETE /class_sessions/{session_id}` usa el soft delete genérico, pero `ClassSession` no implementa `SoftDeleteMixin`. La ruta no expresa la política funcional y asigna atributos que no forman parte del mapping persistente.

Unificarla con la transición a `cancelled`, definir las condiciones permitidas y conservar Bookings.

### FF-FOLLOW-05 — Revisar endpoints de baja con validaciones defectuosas

Los endpoints de GymClass y Membership recuperan una instancia en una variable, pero validan el objeto CRUD en lugar del resultado. Esto puede ocultar un `not found` y pasar valores nulos o incorrectos a `remove()`.

Revisar también Teacher y ClassSchedule para uniformar autorización, respuesta, transacción y semántica de desactivación.

## Prioridad 2 — ORM y esquema pendientes

### FF-FOLLOW-06 — RRULE para ClassSchedule

Implementar el ADR de RRULE como cambio funcional separado: columna nueva, validación, backfill, actualización de services/schemas y retiro de `days_of_week` solo cuando la transición esté completa.

No incorporar todavía `created_by_id` ni `updated_by_id`; la auditoría por actor continúa como decisión pendiente.

### FF-FOLLOW-07 — Historial de Membership

El mapping vigente continúa siendo 1:1. Evaluar el paso a 1:N únicamente con reglas claras para membresía actual, superposición de períodos, cancelación y consultas históricas.

### FF-FOLLOW-08 — Defaults, checks y timestamps

Revisar qué invariantes deben existir también en PostgreSQL:

- defaults de estados y capacidades;
- checks de duración/capacidad restantes;
- actualización de `updated_at` fuera del ORM;
- nullability de discriminadores y contratos Pydantic.

Cada cambio aprobado debe producir una migración pequeña y una comparación Alembic sin drift no explicado.

### FF-FOLLOW-09 — Estrategia Alembic histórica

Las revisiones antiguas contienen `TRUNCATE ... CASCADE`, `DROP TYPE ... CASCADE` y downgrades incompletos. No reescribir migraciones aplicadas. Probar periódicamente una reconstrucción desde cero y evaluar un baseline/squash futuro con procedimiento explícito de adopción.

## Prioridad 3 — arranque y configuración

### FF-FOLLOW-10 — Hacer explícita la dependencia de Redis

La importación de la aplicación requiere `REDIS_URL`, incluso en validaciones que no usan Redis. Decidir si Redis es obligatorio en todos los perfiles o si el cliente debe inicializarse de forma diferida. Documentar la configuración mínima de desarrollo y tests.

### FF-FOLLOW-11 — Completar pruebas de loaders async

Las relaciones ORM usan `lazy="raise"`. Auditar routers, services y CRUD para asegurar que todas las respuestas con relaciones usan `selectinload()` u otra estrategia explícita. Agregar pruebas API que detecten `MissingGreenlet`, N+1 y relaciones no precargadas.

## Orden sugerido

1. FF-FOLLOW-01 y FF-FOLLOW-02.
2. ADR de ciclo de vida (FF-FOLLOW-03).
3. FF-FOLLOW-04 y FF-FOLLOW-05.
4. FF-FOLLOW-10 y FF-FOLLOW-11.
5. RRULE, historial de Membership y ajustes de integridad.
6. Estrategia de baseline Alembic.

## Criterio general de salida

- ninguna ruta operativa elimina historia accidentalmente;
- la aplicación y OpenAPI importan con una configuración mínima documentada;
- la base aislada migra desde cero hasta head;
- `alembic check` no detecta drift inesperado;
- las pruebas cubren estados, relaciones async, conservación histórica y concurrencia;
- ningún test utiliza la base de desarrollo.
