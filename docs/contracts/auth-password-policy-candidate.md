# FitFlow #43 — contrato candidato de contraseñas para el onboarding integrado

Estado: CANDIDATE_NOT_ACCEPTED. Responsabilidad #43. Base: `develop@1ae33b225ed7de2a89116a97c97cf30b339fa0ce`; SOURCE_OF_TRUTH v5.3, blob `f36307af0777fd3b493792ad42115fec56ac44b3`. Este contrato implementa la disposición Product acotada en [Issue #43](https://github.com/mauedgar/FitFlow/issues/43#issuecomment-6582023324); no reemplaza la SOT ni constituye aceptación.

## Altas públicas sin escalamiento de privilegios

- `POST /api/v1/users/register` conserva el registro **legacy de cuenta solamente**, con `email`, `password`, `full_name` opcional; no crea Person/Client. Los campos de rol privilegiado siguen prohibidos para el solicitante.
- `POST /api/v1/users/register-client` conserva el registro **transaccional User + Person/Client** aceptado por #99. Exige `first_name` y `last_name` separados, preserva apellidos compuestos y asigna CLIENT en el servidor. Los datos se confirman en una única transacción; ante error no queda registro parcial.
- **Ambos** esquemas públicos, así como `UserCreate` y `UserUpdate` internos, validan nuevas contraseñas de **máximo 72 bytes UTF-8, sin NUL** antes del acceso a CRUD. Longitudes en bytes, no caracteres. 72 bytes se aceptan, más de 72 o NUL generan HTTP **422** en registro; duplicate-email HTTP 400, éxito HTTP 201. Este cambio desde la aceptación heredada de bcrypt que truncaba es **material e intencional**. La política de longitud mínima no se altera.
- Frontend: conservar nombre y apellido independientes y el único POST `/users/register-client`; mostrar la política de bytes y traducir los 422 del campo password a texto seguro. Nunca mostrar objetos crudos ni registrar contraseñas.

## Compatibilidad con cuentas y hashes anteriores

- `verify_password` preserva hashes bcrypt `$2a$`, `$2b$`, `$2y$` creados anteriormente, incluso contraseñas de más de 72 bytes, sin rehash automático. `get_password_hash` genera únicamente `$2b$12$`, sin truncar nuevas credenciales.
- Los hashes bcrypt de nuevas contraseñas de exactamente 72 bytes conservan la ambigüedad intrínseca del algoritmo: verificar una cadena con sufijo también puede resultar verdadero si comparte los primeros 72 bytes. Esta limitación no se declara resuelta ni se altera silenciosamente el contrato de cuentas antiguas.
- Hash almacenado corrupto o no ASCII falla cerrado con 401 en login, no 500, sin emitir tokens/refresh. JWT, roles, `/users/{id}/public` ADMIN-only, otras rutas y modelos persistentes no se modifican.
- Las credenciales, contraseñas y hashes existentes no se leen ni reescriben. No se habilita un endpoint público de cambio de contraseña; `UserUpdate` es validación interna. Recuperación voluntaria futura usa nueva política, sin reset masivo.

## Gate de aceptación

Solo datos sintéticos y PostgreSQL/Redis desechables: tests HTTP 422 en **los dos** endpoints antes del lookup; 201/400 de alta y perfil actual, 401/403 de identidad, login legacy, hashes erróneos, unicode/NUL/72 bytes, rollback sintético Passlib antiguo → bcrypt nuevo y en sentido inverso. `uv lock --check`, export/requirements consistentes, CI exacta SHA/tree, frontend y Ruff/Pyright acotados. Una IR independiente nueva debe dar **0 findings/0 advisories** en el candidato compuesto; después, aceptación e integración Product explícitas y separadas. Los CI/IR del viejo PR #51 no se trasladan.

No se autoriza desplegar, tocar datos retenidos, integrar #48/#51/#83 ni adoptar CPython 3.15 por este candidato.

## Disposición de recuperación y transición de credenciales heredadas (propuesta)

- **Sin recuperación automática en este candidato.** No existe un flujo público de restablecimiento aprobado; no inventar un endpoint, enviar contraseñas por correo, revelar si una cuenta existe ni alterar usuarios retenidos. Ante una credencial heredada que no pueda validarse con seguridad, la persona deberá usar un procedimiento de soporte/recuperación de identidad **que se diseñará y aprobará por separado** antes de habilitarlo.
- **Verificación heredada limitada al inicio de sesión.** Mantener la comprobación compatible de hashes `$2a$`/`$2b$`/`$2y$` sin truncar manualmente la entrada ni normalizar bytes. Los hashes bcrypt no codifican la longitud original: un login válido con entrada de más de 72 bytes puede coincidir con el prefijo de otra entrada. Por ello, un resultado bcrypt válido **no demuestra que el sufijo sea idéntico** y no autoriza migración o rehash silencioso.
- **Credenciales nuevas o rotadas:** exigir máximo 72 bytes UTF-8 y ausencia de NUL, aplicar la política mínima vigente y producir únicamente hashes nuevos con la configuración aceptada. Una futura rotación debe exigir autenticación/revalidación de identidad apropiada, autorización de la operación, protección contra abuso, revocación de sesiones según el contrato JWT y pruebas de no enumeración; ninguna de esas capacidades se declara implementada aquí.
- **Salida operativa segura:** si el usuario no puede autenticarse, no se propone cambiar directamente el hash en base de datos. Registrar la necesidad de un flujo recuperable con verificación de identidad y revisión de seguridad independiente. Evitar mensajes que expongan el estado del hash, la longitud histórica o la existencia de la cuenta.
- **Prueba y aceptación:** usar exclusivamente usuarios sintéticos y servicios descartables para casos 72/73 bytes, prefijo compartido, `$2a$`/`$2b$`/`$2y$`, hash corrupto, fallos cerrados y ausencia de rehash. El procedimiento real de recuperación y cualquier actualización de credenciales persistidas requieren un candidato y una autorización Product propios.
