---
document_id: FF-QUALITY-001
status: canonical
machine_context: true
version: 5.0
updated: 2026-08-18
---

# Calidad y validación

## Principio

Una modificación no completa una tarea. Debe existir evidencia reproducible,
asociada al scope y a la revisión validada.

## Suites backend

| Carpeta | Cobertura |
| --- | --- |
| `smoke/` | arranque y dependencias básicas |
| `unit/` | reglas puras, services y schemas aislables |
| `integration/` | DB, CRUD, transacciones y fixtures reales |
| `api/` | HTTP, auth, status y contratos |
| `concurrency/` | carreras, locks y sobreventa |

Convenciones: tests deterministas, un comportamiento principal, sin red externa
salvo integración explícita y sin dependencia de orden.

## Comandos canónicos

Desde la raíz:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/quality/run_backend_tests.ps1
powershell -ExecutionPolicy Bypass -File scripts/quality/run_backend_validation.ps1
```

Los wrappers usan exclusivamente Compose `fitflow-test` y la base
`fitflow_test`; no el Python local ni la DB de desarrollo.

## Gates por cambio

| Impacto | Evidencia mínima |
| --- | --- |
| docs/prompts | schemas, links, reglas contradictorias, revisión de diff |
| schema | válidos/inválidos y contrato OpenAPI afectado |
| service | reglas y errores de dominio; unit tests cuando sean aislables |
| CRUD/DB | integración, atomicidad, rollback y concurrencia si aplica |
| router | API, auth, status y mapeo de errores |
| frontend | contrato backend, estados UI/cache y test disponible |
| migracion | upgrade/downgrade seguro en DB de test y revision del desarrollador |

Todo cambio de código incluye, según alcance: targeted tests, suite amplia por
riesgo, Ruff, Pyright, Alembic/OpenAPI y revisión del diff.

## Estados

- `PASS`: ejecutado satisfactoriamente.
- `FAIL`: fallo reproducible.
- `NOT_RUN`: no ejecutado, con causa.
- `UNAVAILABLE`: herramienta o entorno no disponible.
- `BLOCKED`: gate impedido por decisión/riesgo/dependencia.
- `N/A`: no aplica; requiere justificación.

No convertir `NOT_RUN` o `UNAVAILABLE` en `PASS` por inferencia.

## Riesgo

- `low`: validación dirigida y reviewer.
- `medium`: validación dirigida + suite afectada + reviewer independiente.
- `high`: no se ejecuta autónomamente.

Cambios en auth, permisos, transacciones críticas, migraciones destructivas,
secretos, dependencias base o fronteras arquitectónicas son `high` hasta que una
desarrollador recorte y reclasifique el alcance.

## Independencia

Reviewer y Validator no reutilizan la conclusión del Coder como evidencia. El
Validator ejecuta comandos deterministas; un LLM solo puede diagnosticar un
resultado ya observado.

## Docstrings

Endpoints, funciones públicas, métodos CRUD, services y helpers no triviales
requieren docstring breve que describa contrato o comportamiento, no la sintaxis.
