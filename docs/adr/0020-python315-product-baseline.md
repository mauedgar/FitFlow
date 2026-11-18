---
document_id: FF-ADR-0020
status: proposed
machine_context: true
version: 0.2
updated: 2026-11-17
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

Las ruedas de Python3.15 para paquetes con extensiones nativas deben resolverse e instalarse en GitHub Actions o runtime equivalente, incluyendo pydantic-core, greenlet, asyncpg, bcrypt, cffi y psycopg[binary] (Psycopg 3). La aplicacion usa `postgresql+asyncpg` y el migrador de Alembic usa conexion sincronica `postgresql+psycopg`; no se declara necesario Psycopg 2. No declarar compatibilidad basada en marcadores o sdist sin instalación reproducible.

Verificar `uv lock --check`, los exports, importación FastAPI/Pydantic, suite backend con PostgreSQL15/Redis7 efímeros, migraciones Alembic, Ruff/Pyright, frontend y seguridad bcrypt. Distinguir E2E sintético de staging/TLS/retención Redis reales.

## Disposicion acotada de observaciones IR003 (PR #113)

Estas observaciones corresponden a `FITFLOW-C014-PR113-PY3152-FULL-IR003-20261117-001` sobre `72b55048614436b5e1e8980252b92b1b0a4a9f58`. El resultado original 0 findings bloqueantes / 4 advisories permanece historico e inmutable; este documento **no** lo convierte en 0 advisories ni en aceptacion Product. La nueva revision debera evaluar el commit sucesor por separado.

- **A01 — reproducibilidad, alcance calificado:** conservar como evidencia las Actions originales del candidato, el lock/export de `uv` y la instalacion y pruebas con CPython 3.15.2 en Linux, Windows y Docker. No afirmar auditoria exhaustiva del codigo fuente, hashes publicados o cualquier plataforma futura. Antes de adoptar otro host/arquitectura, calificar instalacion locked, artefactos binarios y regresiones en esa plataforma. No se identifico un defecto concreto del lock dentro de las plataformas probadas.
- **A02 — entorno real no ejecutado:** el contrato M4 de preflight no es un smoke real. Mantener `STAGING_SMOKE_NOT_RUN` y **STOP obligatorio** antes de despliegue, reset de fixtures, migraciones sobre datos retenidos o accion equivalente. Se requieren ownership, aislamiento, host CPython 3.15.2, identidad exacta de release, precondiciones de datos y autorizacion operativa independiente. Ninguna CI verde concede ese permiso.
- **A03 — riesgo bcrypt heredado:** preservar verificacion de hashes `$2a---
document_id: FF-ADR-0020
status: proposed
machine_context: true
version: 0.2
updated: 2026-11-17
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

Las ruedas de Python3.15 para paquetes con extensiones nativas deben resolverse e instalarse en GitHub Actions o runtime equivalente, incluyendo pydantic-core, greenlet, asyncpg, bcrypt, cffi y psycopg[binary] (Psycopg 3). La aplicacion usa `postgresql+asyncpg` y el migrador de Alembic usa conexion sincronica `postgresql+psycopg`; no se declara necesario Psycopg 2. No declarar compatibilidad basada en marcadores o sdist sin instalación reproducible.

Verificar `uv lock --check`, los exports, importación FastAPI/Pydantic, suite backend con PostgreSQL15/Redis7 efímeros, migraciones Alembic, Ruff/Pyright, frontend y seguridad bcrypt. Distinguir E2E sintético de staging/TLS/retención Redis reales.

/`$2b---
document_id: FF-ADR-0020
status: proposed
machine_context: true
version: 0.2
updated: 2026-11-17
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

Las ruedas de Python3.15 para paquetes con extensiones nativas deben resolverse e instalarse en GitHub Actions o runtime equivalente, incluyendo pydantic-core, greenlet, asyncpg, bcrypt, cffi y psycopg[binary] (Psycopg 3). La aplicacion usa `postgresql+asyncpg` y el migrador de Alembic usa conexion sincronica `postgresql+psycopg`; no se declara necesario Psycopg 2. No declarar compatibilidad basada en marcadores o sdist sin instalación reproducible.

Verificar `uv lock --check`, los exports, importación FastAPI/Pydantic, suite backend con PostgreSQL15/Redis7 efímeros, migraciones Alembic, Ruff/Pyright, frontend y seguridad bcrypt. Distinguir E2E sintético de staging/TLS/retención Redis reales.

/`$2y---
document_id: FF-ADR-0020
status: proposed
machine_context: true
version: 0.2
updated: 2026-11-17
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

Las ruedas de Python3.15 para paquetes con extensiones nativas deben resolverse e instalarse en GitHub Actions o runtime equivalente, incluyendo pydantic-core, greenlet, asyncpg, bcrypt, cffi y psycopg[binary] (Psycopg 3). La aplicacion usa `postgresql+asyncpg` y el migrador de Alembic usa conexion sincronica `postgresql+psycopg`; no se declara necesario Psycopg 2. No declarar compatibilidad basada en marcadores o sdist sin instalación reproducible.

Verificar `uv lock --check`, los exports, importación FastAPI/Pydantic, suite backend con PostgreSQL15/Redis7 efímeros, migraciones Alembic, Ruff/Pyright, frontend y seguridad bcrypt. Distinguir E2E sintético de staging/TLS/retención Redis reales.

 y de credenciales historicas, sin rehash masivo, reset de usuarios ni cambio de esquema de base. La equivalencia de sufijos tras los primeros 72 bytes es intrinseca al bcrypt almacenado, incluso para nuevas contraseñas de exactamente 72 bytes. Las altas nuevas superiores a 72 bytes UTF-8 y NUL se rechazan; la aceptacion Product explicita de esta compatibilidad/riesgo pertenece al Developer y **no** se infiere de la IR.
- **A04 — aclaracion de driver:** se corrige la referencia obsoleta a `psycopg2`; el manifiesto actual declara `psycopg[binary]==3.3.6`, el migrador usa dialecto sincronico y la aplicacion `asyncpg`. Cualquier cambio posterior de driver requiere CI/migraciones y revision en su propio SHA.

Adopción canónica: **PENDIENTE** de CI+IR+aceptación e integración a `develop`. Si resolución o push quedan bloqueados, conservar el candidato y publicar el recibo original; no reintentar automáticamente.
