# Calidad, testing y validacion

**Estado:** Canonico  
**Version:** 3.0

## 1. Principio

Una task no termina por haber modificado archivos. Debe producir evidencia reproducible.

La suite de tests reduce la cantidad de razonamiento que un agente necesita repetir: un resultado determinista debe preferirse a una inferencia extensa cuando existe un test adecuado.

## 2. Estructura de tests

```text
backend/tests/
├── smoke/          # el harness/app puede arrancar y dependencias basicas funcionan
├── unit/           # reglas puras/services/schemas aislables
├── integration/    # DB/CRUD/transacciones/fixtures reales
├── api/            # contratos HTTP, auth, status codes
├── concurrency/    # carreras/locks/overbooking cuando aplique
├── helpers/
├── factories/
└── _templates/     # ejemplos no recolectables por pytest
```

Convenciones:
- archivos: `test_<area>.py`;
- tests: `test_<behavior>_when_<condition>` o equivalente legible;
- un comportamiento principal por test;
- Arrange / Act / Assert cuando ayude;
- tests deterministas, aislados y sin depender de orden;
- red externa prohibida salvo test explicitamente integrado/mocked;
- fixtures compartidas solo si expresan un concepto estable.

## 3. Markers

Baseline:
- `smoke`
- `unit`
- `integration`
- `api`
- `concurrency`
- `slow`

Ejemplos:

```text
python -m pytest backend/tests -m smoke
python -m pytest backend/tests -m unit
python -m pytest backend/tests -m "integration or api"
```

## 4. Gates por capa

### Modelo/ORM
Mapper config, relaciones/FK/cardinalidad, constraints, typing, impacto Alembic y tests.

### Schema
Casos validos/invalidos, Create/Update/Public/Internal, OpenAPI/response contracts.

### Service
Reglas de negocio y errores de dominio; unit tests cuando sea posible.

### CRUD/transaccion
Atomicidad, rollback/flush/refresh, locks/concurrencia, duplicados, integration tests.

### Router
Roles, status codes, request/response, mapeo DomainError -> HTTP; API tests.

### Frontend
Contrato backend actual, estados de UI/cache y tests de flujo cuando exista cobertura.

## 5. Booking como primer vertical slice

Prioridad inicial:
- duplicado;
- overbooking/capacidad;
- membership/allowed_plan;
- estados invalidos de session;
- atomicidad/transaccion;
- mapping HTTP relevante.

No todo debe ser unit test: reglas comerciales pueden vivir en unit; atomicidad/concurrencia requiere integration/concurrency.

## 6. Comandos canonicos

Desde raiz:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/quality/run_backend_tests.ps1
powershell -ExecutionPolicy Bypass -File scripts/quality/run_backend_validation.ps1
```

Fallback:

```text
python -m pytest backend/tests
```

El Task `testing-baseline` debe reconciliar estos wrappers con el entorno real y dependencia manager existente.

## 7. Estados de evidencia

- **PASS:** ejecutado y satisfactorio.
- **FAIL:** fallo reproducible.
- **NOT_RUN:** no se ejecuto; explicar por que.
- **UNAVAILABLE:** herramienta/configuracion no disponible; constituye gap explicito.
- **A_REVIEW:** evidencia insuficiente/contradictoria.

## 8. Definition of Done para task con codigo

Segun alcance:
1. implementacion dentro del scope;
2. targeted tests;
3. suite mas amplia cuando el riesgo lo justifique;
4. Ruff;
5. Pyright/Pylance o equivalente;
6. Alembic/OpenAPI cuando corresponda;
7. diff review;
8. `RESULT.md` con estado de cada gate.

`N/A` es valido cuando un gate no aplica; no es equivalente a `NOT_RUN`.

## 9. Estado de adopcion

La estructura/harness v3 queda definida por esta suite. La cobertura real de FitFlow sigue siendo **pendiente critica** hasta completar la primera task y verificar tests contra el codigo actual.
