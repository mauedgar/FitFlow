# Resultado - SCRUM-29 / TASK-001

**Fecha:** 2026-08-13  
**Baseline Git:** `45e3251331433b3f5c099ad156de0b35c3f96e55`  
**Estado tecnico:** completado para revision manual  
**Commit:** no realizado

## Alcance implementado

- Los wrappers de calidad ejecutan el backend exclusivamente en el proyecto
  Compose `fitflow-test` y la base `fitflow_test`.
- La suite de integracion rechaza una URL que no nombre la base de tests antes de
  abrir una conexion.
- El smoke valida Python 3.11+, carga de `app.db.base`, metadata y configuracion de
  mappers para las nueve entidades activas.
- Se conservaron los tests reales de Booking para cancelacion/re-reserva y
  concurrencia por el ultimo cupo.
- Se actualizaron las instrucciones de ejecucion y el estado documental.

No se modificaron modelos, migraciones, dominio, nombres estructurales ni codigo
de aplicacion.

## Evidencia

| Gate | Estado | Evidencia |
|---|---|---|
| Compose resuelto y aislado | PASS | Servicios `postgres_test` y `backend_test`; red `fitflow-test_test_network`; volumen `fitflow-test_postgres_test_data`; sin puertos publicados. |
| Conexion PostgreSQL | PASS | Usuario `fitflow_test_user`, base efectiva `fitflow_test`. |
| Alembic read-only | PASS | Revision actual y head: `9c3e4f506172`; no se aplicaron migraciones. |
| Smoke exacto | PASS | `python -m pytest backend/tests -m smoke -q`: 2 passed, 9 deselected. |
| Metadata y mappers | PASS | Nueve tablas activas cargadas y `configure_mappers()` sin error. |
| Booking targeted | PASS | 2 passed en `test_booking_database_invariants.py`. |
| Suite backend | PASS | 11 passed con Python 3.11.15, pytest 8.4.1 y pytest-asyncio 1.1.0. |
| Ruff | UNAVAILABLE | El modulo no esta instalado en `backend_test`. |
| Pyright | UNAVAILABLE | El ejecutable no esta instalado en `backend_test`. |
| Migraciones | NOT_RUN | No hubo cambios de modelos, metadata ni migraciones; solo se inspecciono la revision. |
| Limpieza aislada | PASS | Contenedores y red de `fitflow-test` retirados; volumen `fitflow-test_postgres_test_data` conservado. |

## Incidencias de ejecucion

El primer build encontro un error transitorio del cache de Docker Desktop por un
snapshot padre ausente. No se podo cache ni se eliminaron recursos. La imagen
quedo disponible, el inicio posterior funciono y una reconstruccion posterior
finalizo correctamente.

Un primer comando targeted manual uso por error `tests/...` desde `/app` y no
recolecto tests. Se repitio con la ruta real `backend/tests/...` y paso 2/2. Este
error no corresponde a la suite ni al wrapper canonico.

## Criterios Jira

- PASS: comando de smoke requerido.
- PASS: pytest-asyncio configurado y usado por tests async.
- PASS: estrategia de DB aislada y guard explicito del nombre de base.
- PASS: regla real de Booking cubierta con tests significativos.
- PASS: wrappers alineados con Docker Desktop y el entorno real.
- PASS: resultados registrados sin interpretar tooling ausente como exito.
- PASS: ningun cambio funcional ajeno al testing.

## Riesgos y deuda pendiente

- Ruff y Pyright deben incorporarse en una decision posterior sobre dependencias
  de desarrollo; no se instalaron dentro de TASK-001.
- La cobertura sigue limitada y no demuestra el startup HTTP completo.
- Los tests usan UUID unicos y son repetibles, pero conservan datos de prueba en
  el volumen aislado hasta que exista una politica aprobada de limpieza.
- Al iniciar la tarea, `fitflow-backend-1` ya figuraba `Exited (1)`; no se lo
  inicio, reinicio, recreo ni modifico.

## Recursos protegidos

No se modificaron los contenedores, redes, volumenes ni datos del entorno de
desarrollo. La limpieza de cierre retiro los contenedores y la red del proyecto
`fitflow-test`; su volumen permanece disponible. Al finalizar, PostgreSQL de
desarrollo continuaba healthy, Adminer continuaba activo y el backend conservaba
su estado preexistente `Exited (1)`.

## Actualización posterior

En SCRUM-32, Ruff y Pyright se incorporaron a la imagen de tests. Ruff y Pyright
pasaron de `UNAVAILABLE` a herramientas ejecutables; sus fallos actuales se
registran como `FAIL` de calidad, no como indisponibilidad.
