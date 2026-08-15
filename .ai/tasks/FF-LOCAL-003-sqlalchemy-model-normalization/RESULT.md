# Resultado - SCRUM-31 / TASK-003

**Fecha:** 2026-08-13  
**Estado:** completada para revisión  
**Baseline:** working tree posterior a SCRUM-29/SCRUM-30  
**Commit:** no realizado

## Resultado ejecutivo

La auditoría del código ejecutable demuestra que los nueve modelos ORM activos
ya utilizan el estilo declarativo SQLAlchemy 2.x: `Mapped[T]`,
`mapped_column(...)` y relaciones anotadas con `Mapped[...]`. No había columnas
legacy `Column(...)` pendientes de convertir. Por esa razón no se aplicaron
transformaciones mecánicas artificiales ni se tocaron archivos de producción.

Se preservaron exactamente nombres de tablas/columnas, tipos SQL, nullability,
defaults, índices, claves foráneas, cardinalidades, cascades, enums y mixins.
`Role`, `Permission` y `role_permissions` continúan fuera del registro ORM
activo como legado RBAC, según las decisiones vigentes.

## Evidencia por modelo

| Modelo | Archivo | Estado |
|---|---|---|
| User | `backend/app/db/models/user.py` | `Mapped`/`mapped_column`; relación opcional preservada |
| Person | `backend/app/db/models/person.py` | `Mapped`/`mapped_column`; herencia y FK preservadas |
| Client | `backend/app/db/models/client.py` | `Mapped`/`mapped_column`; relaciones preservadas |
| Teacher | `backend/app/db/models/teacher.py` | `Mapped`/`mapped_column`; herencia y relación preservadas |
| Membership | `backend/app/db/models/membership.py` | mapping 2.0 completo |
| GymClass | `backend/app/db/models/gym_class.py` | mapping 2.0 completo |
| ClassSchedule | `backend/app/db/models/class_schedule.py` | mapping 2.0 completo; RRULE no agregado |
| ClassSession | `backend/app/db/models/class_session.py` | mapping 2.0 completo; cascades sin cambios |
| Booking | `backend/app/db/models/booking.py` | mapping 2.0 completo; unicidad y FK sin cambios |

La base declarativa `backend/app/db/base_class.py` usa `DeclarativeBase` y los
mixins existentes ya usan `Mapped`/`mapped_column` correctamente.

## Validaciones

- **PASS** — `pytest` ORM/smoke: 9 passed.
- **PASS** — Booking integration targeted: 2 passed.
- **PASS** — metadata y mappers: incluidos en los tests ORM/smoke.
- **FAIL preexistente** — Ruff sobre el proyecto: 261 errores; sobre modelos:
  23 errores, principalmente `EXE002`, imports y `RUF100`. No se corrigieron
  porque exceden la normalización declarativa y no cambian el mapping.
- **FAIL/UNAVAILABLE** — Pyright instalado pero no ejecutable: Node no carga
  `libatomic.so.1` dentro de la imagen.
- **NOT_RUN** — Alembic; TASK-003 no genera migraciones y no cambia metadata.
- **PASS** — no se detectaron `Column(...)` legacy en los modelos activos.

## Ambigüedades derivadas a TASK-004

- No se modificaron nulabilidades que pudieran implicar una decisión de dominio.
- No se modificaron cardinalidades, `delete-orphan`, `ON DELETE`, ownership ni
  políticas de borrado.
- Los riesgos funcionales de cascades y rutas DELETE quedan para SCRUM-32.

## Archivos modificados

No se modificaron modelos ni código de aplicación. Solo se creó este reporte de
resultado. Se conservaron todos los cambios previos del working tree.

## Criterios Jira

- Estilo SQLAlchemy 2.x: **PASS por estado ya existente**.
- Semántica persistente preservada: **PASS**.
- Sin cambios de integridad/negocio: **PASS**.
- Mapper/import smoke: **PASS**.
- Pytest targeted: **PASS**.
- Ruff: **FAIL preexistente documentado**.
- Type-check: **UNAVAILABLE por dependencia del runtime**.
