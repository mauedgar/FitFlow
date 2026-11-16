# FitFlow #43/#44 — contrato candidato de bcrypt y contraseñas (PR #113)

Estado: CANDIDATE_NOT_ACCEPTED. Responsabilidades #43 y #44; [PR #113](https://github.com/mauedgar/FitFlow/pull/113) es el candidato **aislado de Python 3.15.2 y bcrypt**, con base congelada `develop@c8bedd52cc3663f773dbe623f381c83392893dce`; SOURCE_OF_TRUTH v5.3, blob `f36307af0777fd3b493792ad42115fec56ac44b3`. Este contrato adopta solo el alcance acotado de bcrypt y compatibilidad de contraseñas de [Issue #43](https://github.com/mauedgar/FitFlow/issues/43#issuecomment-6582023324); **no** incorpora los cambios de logout/JWT/sesiones ni las modificaciones de frontend de PR #107. No reemplaza la SOT ni constituye aceptación.

## Altas públicas sin escalamiento de privilegios

- `POST /api/v1/users/register` conserva el registro **legacy de cuenta solamente**, con `email`, `password`, `full_name` opcional; no crea Person/Client. Los campos de rol privilegiado siguen prohibidos para el solicitante.
- `POST /api/v1/users/register-client` conserva el registro **transaccional User + Person/Client** aceptado por #99. Exige `first_name` y `last_name` separados, preserva apellidos compuestos y asigna CLIENT en el servidor. Los datos se confirman en una única transacción; ante error no queda registro parcial.
- **Ambos** esquemas públicos, así como `UserCreate` y `UserUpdate` internos, validan nuevas contraseñas de **máximo 72 bytes UTF-8, sin NUL** antes del acceso a CRUD. Longitudes en bytes, no caracteres. 72 bytes se aceptan, más de 72 o NUL generan HTTP **422** en registro; duplicate-email HTTP 400, éxito HTTP 201. Este cambio desde la aceptación heredada de bcrypt que truncaba es **material e intencional**. La política de longitud mínima no se altera.
- Contrato de frontend **existente y fuera del write-set de PR #113**: conservar nombre/apellido independientes y el único POST `/users/register-client`; presentar respuestas 422 seguras y nunca registrar contraseñas. Cualquier adaptación de interfaz adicional requiere PR y revisión independientes; este candidato no la implementa.

## Compatibilidad con cuentas y hashes anteriores

- `verify_password` preserva hashes bcrypt `$2a$`, `$2b$`, `$2y$` creados anteriormente, incluso contraseñas de más de 72 bytes, sin rehash automático. `get_password_hash` genera únicamente `$2b$12$`, sin truncar nuevas credenciales.
- Los hashes bcrypt de nuevas contraseñas de exactamente 72 bytes conservan la ambigüedad intrínseca del algoritmo: verificar una cadena con sufijo también puede resultar verdadero si comparte los primeros 72 bytes. Esta limitación no se declara resuelta ni se altera silenciosamente el contrato de cuentas antiguas.
- Hash almacenado corrupto o no ASCII falla cerrado con 401 en login, no 500, sin emitir tokens/refresh. JWT, roles, `/users/{id}/public` ADMIN-only, otras rutas y modelos persistentes no se modifican.
- Las credenciales, contraseñas y hashes existentes no se leen ni reescriben. No se habilita un endpoint público de cambio de contraseña; `UserUpdate` es validación interna. Recuperación voluntaria futura usa nueva política, sin reset masivo.

## Gate de aceptación

Solo datos sintéticos y PostgreSQL/Redis desechables: tests HTTP 422 en **los dos** endpoints antes del lookup; 201/400 de alta y perfil actual, 401/403 de identidad, login legacy, hashes erróneos, unicode/NUL/72 bytes, rollback sintético Passlib antiguo → bcrypt nuevo y en sentido inverso. `uv lock --check`, export/requirements consistentes, CI exacta SHA/tree, frontend y Ruff/Pyright acotados. Una IR independiente del **candidato aislado PR #113 sobre su HEAD/TREE propio** debe permitir justificar los findings y advisories de alcance bcrypt/Python; cualquier observación abierta exige disposición documentada. Después siguen aceptación e integración Product explícitas y separadas, sin transferir las IR del compuesto PR #107. Los CI/IR del viejo PR #51 no se trasladan.

No se autoriza desplegar, tocar datos retenidos ni integrar #48/#51/#83/#107/#109 automáticamente. CPython 3.15.2 se propone como baseline principal de FitFlow, pero **solo será canónico en `develop` tras la aceptación Developer y una integración competente no forzada**; este documento por sí solo no lo promueve.
