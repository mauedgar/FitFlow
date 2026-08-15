# FitFlow - Agent Operating Guide

Este archivo es la entrada operativa para agentes de codigo. Debe mantenerse pequeno, estable y alineado con `docs/`.

## 1. Objetivo actual

FitFlow es un sistema de gestion de gimnasio. El objetivo inmediato es **cerrar Sprint 6.8 y alcanzar un MVP operativo** sin abrir otra cadena de refactors laterales.

No asumas que una capacidad objetivo ya esta implementada solo porque aparezca en un ADR, roadmap o documento historico.

## 2. Fuente de verdad

Usa esta jerarquia:

1. **Codigo + tests + configuracion + migraciones vigentes**: realidad ejecutable.
2. **`docs/current-state.md`**: snapshot consensuado del estado actual.
3. **`docs/architecture.md` y `docs/domain.md`**: responsabilidades, fronteras e invariantes.
4. **`docs/adr/`**: decisiones aceptadas, incluidas las pendientes de implementar.
5. **`docs/roadmap.md`**: direccion futura.
6. **Indices, RepoMap, caches y bundles**: artefactos derivados; sirven para localizar, no para reemplazar la lectura del codigo antes de editar.
7. **`docs/archive/`**: material historico/superseded; no usar por defecto.

Si dos fuentes activas se contradicen, no resuelvas la contradiccion en silencio. Verifica el codigo y registra la discrepancia como **A revisar**.

## 3. Estructura canonica del backend

```text
backend/app/
├── routers/       # HTTP, DI, auth/roles, status codes y mapeo de errores
├── schemas/       # contratos Pydantic v2 y validacion estructural
├── services/      # reglas de negocio, calculos y orquestacion
├── crud/          # acceso a datos y operaciones transaccionales
├── db/
│   ├── models/    # modelos SQLAlchemy 2.x
│   ├── base.py
│   └── base_class.py
└── core/          # configuracion, seguridad y concerns transversales
```

Para tareas backend prioriza Python y estas rutas. Nunca inventes paths: descubre el archivo y usa la ruta exacta encontrada.

## 4. Responsabilidades

```text
Request -> Pydantic Schema -> Router -> Service -> CRUD -> SQLAlchemy Model -> PostgreSQL
```

- **Routers/FastAPI:** HTTP, DI, auth/autorizacion, status codes, OpenAPI y traduccion de errores.
- **Schemas/Pydantic v2:** contratos y validacion estructural; no reglas dependientes de DB.

Convenciones de schemas: `*InResponse` es una vista compacta anidada;
`*Public` es autocontenido y público; `<Class1>In<Class2>Response` representa
`Class1` dentro de `Class2`; y `*WithRelations` requiere relaciones cargadas
explícitamente. Mantener estos sufijos al crear contratos nuevos.
- **Services:** propietarios de las reglas de negocio.
- **CRUD:** persistencia, consultas y limites transaccionales; no decide politicas de negocio.
- **SQLAlchemy/PostgreSQL:** persistencia e integridad estructural.
- **Redis:** estado temporal/infraestructura cuando corresponda.

Arquitectura objetivo: **monolito modular**, implementado de forma incremental y sin big-bang refactor durante el MVP.

## 5. Dominio operativo

```text
User -> Person -> Client / Teacher
Client -> Membership
GymClass -> ClassSchedule -> ClassSession -> Booking
```

Reglas criticas de Booking:
- no duplicar reserva para la misma sesion;
- bloquear sesiones invalidas por estado/tiempo;
- validar membership y compatibilidad de plan;
- capacidad y creacion deben protegerse atomicamente;
- cancelacion != eliminacion;
- cuando aplique, `class_schedule_id XOR class_session_id` es validacion estructural del schema.

**RRULE** es una decision aceptada para `ClassSchedule`, pero su implementacion actual debe verificarse. No la marques como completada solo por documentacion.

## 6. Testing y validacion

El baseline de testing vive en `backend/tests/` y la politica en `docs/quality-and-validation.md`.

Comandos canonicos iniciales desde la raiz:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/quality/run_backend_tests.ps1
powershell -ExecutionPolicy Bypass -File scripts/quality/run_backend_validation.ps1
```

Fallback directo:

```text
python -m pytest backend/tests
```

Una tarea que modifica codigo no termina por haber escrito archivos. Debe reportar **PASS / FAIL / NOT_RUN / UNAVAILABLE** para las validaciones aplicables.

No inventes una suite que no existe. Si falta una fixture, dependencia o configuracion necesaria, marca el gap y mantenlo dentro del scope de la task correspondiente.

## 7. Politica de cambios

- Una tarea = un problema o cambio conceptual delimitado.
- No iniciar refactors laterales por preferencia estetica.
- Antes de renombrar archivos o simbolos, auditar referencias e impacto.
- No cambiar dominio, arquitectura objetivo, dependencias base ni ADRs aceptados sin autorizacion explicita.
- Si un cambio requiere una decision durable nueva, propone un ADR.
- Los hallazgos sin evidencia suficiente son **A revisar**, no defectos confirmados.
- No mezclar cambios de la misma seccion en dos lanes de escritura simultaneas.

## 8. Ciclo de trabajo

Jira es el control de trabajo humano. Git conserva la implementacion. `.ai/tasks/` conserva el contrato operativo y el reporte tecnico.

Estados de referencia:

```text
Backlog -> Ready -> In Progress -> Validation -> Review -> Done
                         \-> Blocked
```

Dimensiones:
- area: `backend`, `frontend`, `infra`, `docs`, `ai-tooling`;
- execution lane: `human`, `codex`, `aider`, `mixed`, `undecided`;
- type: `feature`, `fix`, `refactor`, `audit`, `test`, `docs`, `tooling`.

Ver `docs/process/task-lifecycle-and-reporting.md`.

## 9. Desarrollo asistido por IA

FitFlow mantiene dos pipelines complementarios:

1. **Codex + Project Index**: pipeline principal para tareas complejas y auditorias. El indice aporta candidatos reutilizables; Codex verifica la fuente real antes de editar.
2. **AiderDesk local**: rama operativa independiente. M-Explorer localiza evidencia; Worker implementa cambios acotados; Reviewer valida.

El resultado de explorers/indexadores debe ser compacto: ruta, simbolo, rango y motivo. No pasar al Worker todo el historial si la evidencia final es suficiente.

## 10. Documentos a consultar

- Estado actual: `docs/current-state.md`
- Arquitectura: `docs/architecture.md`
- Dominio: `docs/domain.md`
- Roadmap: `docs/roadmap.md`
- Calidad/testing: `docs/quality-and-validation.md`
- Proceso/tasks/reportes: `docs/process/`
- IA/contexto: `docs/ai/`
- Decisiones: `docs/adr/`

No consultes `docs/archive/` por defecto.
Do not inspect or modify these paths unless explicitly requested:
- .venv_tools/
- .venv/
- .venv_backend/
- node_modules/
- dist/
- coverage/
- logs/
- historical/
- internal/
- scripts/generated/
- .env
- .env.*
## 11. Normas de Código (Coding Standards)

- **Docstrings obligatorios**: Cada función o método creado o modificado **must** incluir un docstring breve.
- **Anotaciones**: Usa tipado explícito (`__anotated__`) en los parámetros y retornos de las funciones.
- **Formato de docstring**: Mantén una descripción de una o dos líneas que resuma la acción de la función.