# FitFlow #97 — DocImpact: autorregistro cliente transaccional (candidato, 2026-11-07)

## Autoridad y alcance
- Product SOT: `docs/SOURCE_OF_TRUTH.md` v5.3, blob `f36307af0777fd3b493792ad42115fec56ac44b3`.
- Baseline: `develop@a2ae78dff1f3022df8e6a963e4a4cf2b36f2fb48`, tree `66bd4dc8fb98b6702fd2ce9962cba692a38ff3c0`.
- Issue: #97; un candidato no es aceptación ni autorización para desplegar, integrar o migrar datos históricos.

## Contrato de transición
La interfaz de nuevo cliente usa `POST /api/v1/users/register-client`. Su entrada contiene `email`, `password` y `full_name` obligatorio (al menos nombre y apellido, longitud 3–200, espacios normalizados). `extra=forbid` rechaza `role` incluso si se envía `client`. La contraseña se procesa con el mismo hashing existente que el registro anterior; la asignación del rol `client` ocurre exclusivamente del lado servidor.

En una transacción SQL se crean `User`, `Person` y `Client` por joined inheritance; un error en cualquiera de las escrituras revierte todas. Se devuelve `UserPublic` sin contraseñas. La validación de email único sigue cubierta por preconsulta y restricción SQL; no se promete persistencia si ocurre una carrera.

`POST /api/v1/users/register` **permanece sin cambios** como contrato legado de creación de cuenta aislada, sin `Person/Client`. No se fabrican perfiles a partir de nombres ausentes ni se rehacen registros históricos; las cuentas antiguas sin perfil siguen requiriendo intervención Product separada. La UI pública de registro sí migra al nuevo endpoint; su campo visible pasa a pedir nombre y apellido. Los clientes nuevos pueden consultar `/clients/me` con JWT autenticado sin alta administrativa adicional.

## Seguridad y regresión
- No se modifica `GET /users/public`, `GET /users/{id}/public`, las mutaciones de GymClass ni `/auth/me`: se preserva el contrato P0 integrado por PR #95.
- No hay cambios a bcrypt/Passlib, JWT, Redis, DB schema, Alembic, membresías, estados de facturación, permisos de workflow ni secretos.
- Tests propuestos con Postgres `fitflow_test` descartable: respuesta de registro y perfil real, `/clients/me`, rechazo 422 de nombre incompleto e inyección de role, duplicados 400, y fallo inyectado de NOT NULL que revierte User junto con Person/Client; limpieza sintética explícita.
- Se requiere CI exacta backend y frontend y revisión independiente sobre SHA/tree final con 0 findings/0 advisories del candidato. El resultado de CI no autoriza beta.
- La división de `full_name` en `first_name`/`last_name` usa la última palabra como apellido; nombres compuestos complejos pueden requerir modelado explícito futuro. No inferir nombre legal validado.

## Integración con otras ramas
PRs #51, #48, #68 y #83 contienen ediciones de rutas/esquemas/registro y dependen de baselines anteriores. No se modifican esos candidatos aquí. Su futura composición debe conservar `PublicClientRegistration`, la frontera de rol de PR95 y el registro transaccional, sin trasladar CI/IR entre SHA.


## IR001 repairs (new candidate, 2026-11-07)
- A01: `full_name` whitespace normalization occurs with Pydantic `field_validator(mode="before")` so Field length bounds apply to the normalized name. Tests cover raw length over 200 becoming a valid normalized name and an over-limit normalized name rejected 422.
- A02: two simultaneous real HTTP requests are synchronized after separate database prechecks, then race against the unique email index; expect exactly 201/400, one User and one Client, with explicit synthetic cleanup. The transaction now flushes and refreshes before the sole commit.
- A03: the existing disposable signed ADMIN browser workflow additionally runs a separate browser script on local Vite/backend/PG15/Redis7 for actual registration UI, login, signed `/clients/me`, duplicate 400 and validation 422. This extends only test infrastructure, not production secrets/services. Keep any failure as evidence, not an automatic retry.
