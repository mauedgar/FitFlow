---
document_id: FF-ADR-0020
status: proposed
machine_context: true
version: 0.1
updated: 2026-11-04
supersedes: []
---

# ADR 0020 — CPython 3.15.2 como baseline operativo de FitFlow

## Contexto y autoridad

Developer autorizó el 4 de noviembre de 2026 la adopción de la última versión estable de Python y cambios en archivos canónicos y CI. La fuente de verdad sigue siendo `mauedgar/FitFlow`; el objetivo aprobado no constituye por sí mismo implementación canónica.

Se preserva ADR 0018 como historia sobre adopción de uv y su entorno externo. Esta decisión no cambia el ciclo ni la autoridad de Tecnotron.

## Decisión propuesta para integración

- Interpretador Product único CPython **3.15.2**; `.python-version` lo fija para desarrollo y CI, mientras `pyproject.toml` restringe a `>=3.15,<3.16` para permitir actualizaciones de parche calificadas.
- Se retira el soporte Product 3.11, 3.12 y 3.13 una vez que el candidato integrado obtenga CI exacta, IR independiente y aceptación competente. Python3.11 solo puede usarse como intérprete histórico **aislado** en pruebas sintéticas de hashes Passlib y no forma parte del servicio.
- `pyproject.toml` y `uv.lock` son autoridad única de dependencias; los dos exports con hashes son proyecciones regeneradas mediante `uv export --locked`. Prohibidos cambios manuales de hashes.
- Contenedores runtime/build/test deben compartir serie CPython3.15; un solo gate backend completo por candidato, con pruebas especializadas no duplicadas y frontend/Chrome independientes cuando corresponda.
- Actualizaciones de parches posteriores requieren lock reproducible, tests de regresión, compatibilidad de extensiones nativas y aprobación; no se adopta automáticamente una versión mayor ni prerelease.

## Riesgos y validación

Las ruedas de Python3.15 para paquetes con extensiones nativas deben resolverse e instalarse en GitHub Actions o runtime equivalente, incluyendo pydantic-core, greenlet, asyncpg, bcrypt, cffi y psycopg2. No declarar compatibilidad basada en marcadores o sdist sin instalación reproducible.

Verificar `uv lock --check`, los exports, importación FastAPI/Pydantic, suite backend con PostgreSQL15/Redis7 efímeros, migraciones Alembic, Ruff/Pyright, frontend y seguridad bcrypt. Distinguir E2E sintético de staging/TLS/retención Redis reales.

Adopción canónica: **PENDIENTE** de CI+IR+aceptación e integración a `develop`. Si resolución o push quedan bloqueados, conservar el candidato y publicar el recibo original; no reintentar automáticamente.
