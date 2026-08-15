# Resultado - SCRUM-30 / TASK-002

**Fecha:** 2026-08-13  
**Tipo:** auditoría read-only  
**Estado:** completada para revisión  
**Cambios de producción:** ninguno

## Convención real confirmada

La estructura canónica ejecutable es `backend/app/db/models/`; no existe
`backend/app/models/`. Los módulos usan `snake_case` singular para una entidad
(`class_schedule.py`, `class_session.py`, `gym_class.py`, `membership.py`) y
los routers usan plural cuando representan colecciones HTTP (`bookings.py`,
`class_schedules.py`, `class_sessions.py`). Esta diferencia es intencional por
capa y no es un error de naming.

## Inventario y clasificación

| Ruta / símbolos | Patrón observado | Clasificación | Impacto | Acción propuesta |
|---|---|---|---|---|
| `backend/app/db/models/*.py` | Modelos singulares en archivos `snake_case`; registro en `models/__init__.py` | Diferencia intencional/canónica | Bajo; cambiar la ruta rompería imports, Alembic y referencias de tabla | Mantener |
| `backend/app/routers/*.py` | Routers plurales para recursos (`bookings`, `clients`, `class_schedules`) | Diferencia intencional de capa | Bajo; refleja colección HTTP | Mantener |
| `backend/app/services/*_service.py` | Servicios por entidad o concern: `booking_service`, `class_schedule_service`, `front_desk_service` | Convención válida | Bajo | Mantener |
| `backend/app/crud/crud_*.py` | Archivos `crud_<entidad>.py`, clases `CRUD<Entity>` | Convención válida | Bajo | Mantener |
| `backend/app/crud/crud_user.py:30` | Exporta `user_crud`; otros CRUD exportan `booking`, `client`, `teacher`, etc. | Alias compatible / inconsistencia | Medio; obliga aliases distintos en `auth.py`, `client_service.py` y routers | Proponer normalización separada; no renombrar aquí |
| `backend/app/routers/clients.py:18`, `teachers.py:17` | Importan módulo como `crud`; otros routers importan instancia como `*_crud` | Alias compatible / inconsistencia | Medio; reduce trazabilidad y puede confundir módulo con instancia | Normalizar aliases en task posterior |
| `backend/app/schemas/*.py` | Mezcla `Booking`, `Client`, `User` con `*Public`, `*Read`, `*With*`, `*In*Response` | Diferencia contractual / A revisar | Alto si se renombra: afecta response models, imports y OpenAPI | Auditar y decidir en SCRUM-34; no tocar en SCRUM-30 |
| `backend/app/schemas/booking_refs.py:11`, `class_session_refs.py:11`, `teacher_refs.py:8` | Contratos mínimos separados para evitar ciclos | Diferencia intencional | Bajo; eliminar archivos puede reintroducir ciclos Pydantic | Mantener y documentar convención |
| `backend/app/db/models/role.py:7`, `permission.py:7`, `role_permissions.py:3` | Legado RBAC paralelo; no son entidades ORM activas | Nombre legado | Alto si se reactiva o renombra: contradice UserRole y metadata vigente | Excluir del runtime; tratar en ticket RBAC separado |
| `backend/app/schemas/role.py`, `permission.py`, `crud_role.py`, `crud_permission.py` | Contratos/CRUD para RBAC legado sin rutas activas equivalentes | Código legado/no utilizado en el flujo vigente | Medio; imports directos fallan si se usa como ORM | No modificar; retirar solo con decisión explícita |
| `backend/app/db/models/user.py:37`, `schemas/user.py:21` | `UserRole` importado desde el módulo User en schemas, aunque su definición vive en `core.enums` | Alias de compatibilidad / ubicación ambigua | Medio; puede propagar dependencia incorrecta | Normalizar en TASK-005 junto con enums |
| `backend/app/services/errors.py` y `booking_service.py` | Existen excepciones con nombres repetidos (`NotFoundError`, `ConflictError`, etc.) en dos namespaces | Diferencia intencional pero A revisar | Medio; unificación accidental cambiaría mapeo de errores | Mantener hasta auditoría de ownership |
| `backend/app/schemas/class_schedule.py:170` | Import tardío de módulo como `gym_class_schemas` para evitar ciclo | Alias técnico | Bajo/medio; renombrar sin revisar el ciclo rompe importación | Mantener; revisar con TASK-006 |

## Referencias y compatibilidad

- No se encontraron referencias activas a `backend/app/models/`; la ruta
  documentada ejecutable es `backend/app/db/models/`.
- `Base.metadata` registra nueve tablas activas; `Role`, `Permission` y
  `role_permissions` no forman parte del registro ORM.
- Las relaciones usan nombres de entidad coherentes (`class_schedule`,
  `class_sessions`, `bookings`, `membership`, `gym_class`, `teacher`). No se
  propone cambiar relaciones en esta tarea.
- No se detectaron clases públicas duplicadas entre módulos de schemas.
- Los imports internos usan `app...`; no se encontró mezcla ejecutable con
  `backend.app...` en el backend activo.

## Candidatos de renombrado y dependencias

1. `user_crud` -> una convención única (`user` o `user_crud`): afecta
   `auth.py`, `client_service.py` y cualquier import del CRUD de usuarios.
2. Aliases `crud` en `clients.py`/`teachers.py` -> aliases explícitos:
   afecta solo imports locales, pero requiere prueba de importación y smoke.
3. Familias de schemas sin sufijo (`Booking`, `Client`, `User`, etc.): requiere
   inventario de response models/OpenAPI y pertenece a SCRUM-34.
4. `UserRole` reexportado desde `db.models.user`: pertenece a SCRUM-33 y no debe
   resolverse como simple limpieza de imports.

Ningún candidato se implementa en SCRUM-30 por la restricción read-only y por el
riesgo de alterar contratos públicos, ciclos de importación o tareas posteriores.

## Decisiones aplicadas posteriormente con aprobación humana

- La instancia de `CRUDUser` se normalizó a `user`; los consumidores importan
  `user as user_crud` cuando un nombre local `user` evitaría la colisión.
- `clients.py` y `teachers.py` conservan aliases explícitos por entidad, no el
  alias genérico `crud`.
- Las convenciones de schemas anidados quedaron documentadas en `AGENTS.md` y
  `docs/architecture.md`; la consolidación contractual completa sigue en
  SCRUM-34.

## Validaciones

- PASS: inventario AST de routers, schemas, services, CRUD y modelos.
- PASS: búsqueda de referencias a rutas antiguas y namespaces de imports.
- PASS: revisión de documentación activa y `TASK.md` local.
- PASS: no se modificó código de producción.
- N/A: pytest, Ruff y type-check; la tarea es read-only y el baseline ya fue
  validado en SCRUM-29.
- PASS: `git diff` conserva los cambios previos de TASK-001; no se ejecutaron
  operaciones Git mutantes.

## Follow-up

Proponer una task implementadora independiente para aliases CRUD si la
normalización se aprueba. Mantener schemas, enums, relaciones ORM y RBAC en sus
tareas Jira respectivas. No actualizar `current-state.md` porque esta auditoría
no cambia el comportamiento comprobado ni una decisión arquitectónica.
