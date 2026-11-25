---
document_id: FF-ADR-0020
status: canonical
machine_context: true
version: 0.3
updated: 2026-11-25
supersedes: []
---

# ADR 0020 — CPython 3.15.2 como baseline operativo de FitFlow

## Contexto y autoridad

Developer autorizó el 4 de noviembre de 2026 la adopción de la última versión estable de Python y cambios en archivos canónicos y CI. La fuente de verdad sigue siendo `mauedgar/FitFlow`; el objetivo aprobado no constituye por sí mismo implementación canónica.

Se preserva ADR 0018 como historia sobre adopción de uv y su entorno externo. Esta decisión no cambia el ciclo ni la autoridad de Tecnotron.

## Decisión adoptada e integrada en PR #113

- Interpretador Product único CPython **3.15.2**; `.python-version` lo fija para desarrollo y CI, mientras `pyproject.toml` restringe a `>=3.15,<3.16` para permitir actualizaciones de parche calificadas.
- Se retira el soporte Product 3.11, 3.12 y 3.13 conforme a la aceptación e integración acotada de PR #113. Esta decisión no califica otros entornos ni candidatos. Python3.11 solo puede usarse como intérprete histórico **aislado** en pruebas sintéticas de hashes Passlib y no forma parte del servicio.
- `pyproject.toml` y `uv.lock` son autoridad única de dependencias; los dos exports con hashes son proyecciones regeneradas mediante `uv export --locked`. Prohibidos cambios manuales de hashes.
- Contenedores runtime/build/test deben compartir serie CPython3.15; un solo gate backend completo por candidato, con pruebas especializadas no duplicadas y frontend/Chrome independientes cuando corresponda.
- Actualizaciones de parches posteriores requieren lock reproducible, tests de regresión, compatibilidad de extensiones nativas y aprobación; no se adopta automáticamente una versión mayor ni prerelease.

## Riesgos y validación

Las ruedas de Python3.15 para paquetes con extensiones nativas deben resolverse e instalarse en GitHub Actions o runtime equivalente, incluyendo pydantic-core, greenlet, asyncpg, bcrypt, cffi y psycopg[binary] (Psycopg 3). La aplicación usa `postgresql+asyncpg` y el migrador Alembic emplea `postgresql+psycopg` para migraciones sincrónicas; este candidato no depende de Psycopg 2. No declarar compatibilidad basada en marcadores o sdist sin instalación reproducible.

Verificar `uv lock --check`, los exports, importación FastAPI/Pydantic, suite backend con PostgreSQL15/Redis7 efímeros, migraciones Alembic, Ruff/Pyright, frontend y seguridad bcrypt. Distinguir E2E sintético de staging/TLS/retención Redis reales.

## Disposición acotada de observaciones IR003 — PR #113

La propuesta histórica corresponde al dictamen original `FITFLOW-C014-PR113-PY3152-FULL-IR003-20261117-001` en `72b55048614436b5e1e8980252b92b1b0a4a9f58`. Preserva su 0F/4A histórico: documentar una disposición **no** transforma retroactivamente los advisories en cero ni concede aceptación Product. La IR004 del sucesor `23d8df8b651be65bf29b48e45750872a5a063b16` informó F01 documental por inserción duplicada; este texto lo reconstruye, sin transferir su veredicto al nuevo SHA.

- **A01 — evidencia reproducible delimitada:** las Actions y el lock/export `uv` calificaron CPython 3.15.2 con Linux, Windows y Docker del candidato. Eso no es una auditoría exhaustiva de ruedas, hashes publicados, plataformas o arquitecturas futuras. Todo nuevo destino exige instalación locked y regresión propia; no se ha demostrado defecto concreto en el lock dentro de las plataformas probadas.
- **A02 — STOP operativo M4:** el preflight de staging no equivale al smoke HTTP real. `STAGING_SMOKE_NOT_RUN` permanece como condición previa obligatoria a despliegue, reset de fixtures, migración o escritura sobre datos retenidos. Requiere un entorno aislado, ownership, release exacto, verificación del intérprete CPython 3.15.2 y autorización independiente. No se ejecuta staging mediante este ADR.
- **A03 — compatibilidad bcrypt heredada:** preservar la verificación de hashes literales `$2a$`, `$2b$` y `$2y$` y credenciales antiguas sin rehash automático ni reset masivo. Bcrypt compara como máximo los primeros 72 bytes: una contraseña con sufijo puede verificar contra un hash existente con ese prefijo, incluso si el hash proviene de una contraseña nueva de 72 bytes. Las altas nuevas de más de 72 bytes UTF-8 y las que contienen NUL se rechazan. Este riesgo recibió aceptación expresa y acotada a PR #113, conforme a la [disposición #44](https://github.com/mauedgar/FitFlow/issues/44#issuecomment-6969613210) y la [aceptación del candidato exacto](https://github.com/mauedgar/FitFlow/pull/113#issuecomment-6969693167). No se declara eliminado, ni se amplía esta excepción a otros candidatos.
- **A04 — driver PostgreSQL:** se corrige el nombre histórico Psycopg 2; el manifiesto usa `psycopg[binary]==3.3.6` para migración sincrónica y `asyncpg` para aplicación. Cambios futuros de dialecto o binario exigen sus propios tests de migraciones y CI exacta.

## Evidencia de adopción canónica (2026-11-18)

PR #113 fue aceptada e integrada en `develop@276481de41f6829e8dd7beed79127e13237b5dcb`. Candidato aceptado `d5fe2df72cad1fab4941bdd7dc789b8ccbccf0f8`, tree `3199e76a9b7fa8661c3b03febbfb04bc78e8444d`; el merge no introdujo diferencias de archivos frente a ese candidato. [Reconciliación #44](https://github.com/mauedgar/FitFlow/issues/44#issuecomment-6969834968).

Seis workflows originales SUCCESS: 44227580626 (backend 389 pruebas y lock/exports; frontend), 44227580015 (bcrypt 54), 44227579836 (Windows/Docker 35 + 35), 44227579837 (ADMIN browser), 44227579962 (schema), 44227579905 (preflight M4). IR005 [ORIGINAL](https://github.com/mauedgar/ts-execution-transport/blob/216c5f5ae75354c7fa33e03133ed8661f28cbab6/results/FITFLOW-C014-PR113-PY3152-IR005-20261118-001/ORIGINAL.md) recomendó la reparación documental acotada, **no** certificó 0F/0A global. La aceptación de PR #113 fue una disposición específica del Developer, sin transferencia automática a otros candidatos.

Adopción canónica: **INTEGRADA**, limitada a la responsabilidad Python/bcrypt de PR #113. La Issue #43 está cerrada en su alcance A07; #44 permanece abierta para normalización, política de actualizaciones y compatibilidad pendiente. No se acredita staging real, release, datos retenidos ni aprobación de beta. El STOP de A02 se conserva. Esta sincronización documental no altera el contrato de runtime, lock, dependencias, ni la decisión histórica.
