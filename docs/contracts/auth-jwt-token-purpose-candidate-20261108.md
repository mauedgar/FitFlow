---
document_id: FF-ISSUE108-JWT-PURPOSE-20261108-001
status: review_required
issue: 108
candidate_pr: 107
acceptance: false
integration: false
---

# JWT purpose isolation: candidate contract, not accepted

A02 security repair is serialized into PR #107 alongside Issues #43/#44, under the explicit developer expansion for Issue #108. This does not import authority from any other project.

New access tokens are signed with `token_use: access`, refresh tokens with `token_use: refresh`. Emitters override a caller's purpose, and refresh never contains role. Both bearer guards reject any refresh-purpose JWT. Refresh/logout handlers reject access-purpose JWT.

Legacy untyped access JWTs remain usable only with a signed nonempty role claim and original valid expiry. Legacy untyped refresh JWTs have no role and remain eligible solely at refresh/logout under existing Redis registration and blacklist semantics. Unknown or mismatched explicit purpose fails closed. Database role remains authoritative for permissions. No existing tokens, hashes, users or retained state are rewritten.

Tests on exclusively disposable PostgreSQL15/Redis7 cover real HTTP bearer denial, login identity compatibility, legacy and typed refresh, logout, blacklist reuse denial, invalid purpose, and forged role authorization. Existing accepted contracts must not regress. No staging/deploy, credential changes or runtime authorization from this document.

Full candidate CI, source review and independent FULL PRODUCT IR at **0 findings/0 advisories** remain mandatory. A01 ruleset repair is a separate guarded operation before any eventual non-forced integration, after explicit Product acceptance.

## IR002 F001: refresh role continuity

The refresh endpoint must resolve the signed subject as a UUID, load the active, non-soft-deleted user from PostgreSQL and sign a new access JWT with that user's **current persisted role**, never a caller-supplied or stale refresh-token role. An inactive, deleted, missing or malformed subject fails closed without issuing a token. The refresh credential still must pass Redis registration and blacklist checks. Synthetic real-HTTP tests verify role continuity across refresh and changed current roles, as well as negative inactive/missing subjects; no retained data is touched. This is a candidate repair, not acceptance of the IR002 finding or Product integration. Historical refresh-minted untyped access tokens lacking role cannot be safely differentiated from legacy refresh credentials and remain denied as bearers; clients must reauthenticate.

## Candidate Redis retention

New refresh-token registrations and new blacklist records use a positive Redis expiry bounded by the cryptographically verified JWT `exp`, rounded up to avoid premature removal. Malformed/expired JWTs cannot generate an unbounded key. This change does **not** migrate or delete any pre-existing retained Redis keys without a separately authorized cleanup procedure; prior records may remain until operational reconciliation. HTTP integration on disposable Redis7 asserts positive TTL for both registration and revocation, and tests assert rejection of malformed expiry. No production Redis access is authorized.

## Frontend JWT claim interpretation — review-required

The React session context now performs an **untrusted local UX check** on JWT expiry, access purpose, subject and supported role before hydrating session state, including legacy untyped access. This is not a cryptographic signature validation and cannot authorize any API action: the backend's signed JWT, active-account and database-role guards remain authoritative. Redis/refresh JWT must never be presented as a local access identity. Signed teacher roles match the backend `teacher` value; historical frontend `trainer` display references are retained until separately reviewed. The decoded `sub` is a UUID and not proof of the user's email; the existing UI profile model still needs separate server-side identity projection if email is shown.

## IR003 F001: authoritative frontend identity

The JWT signed `sub` is a UUID **not an email address**. AuthProvider must treat its locally decoded claims as untrusted UX prechecks only, then use the existing authenticated `GET /auth/me` response to project `currentUser.id`, `currentUser.email`, `currentUser.role` and `currentUser.active`. The returned ID must equal the local JWT subject; disabled/malformed/mismatched profiles and backend errors must fail closed rather than fabricating identity. The ADMIN session gate and query cache key must compare authenticated UUID to the server identity UUID, not email. No new API, database migration, credential or retained state change is permitted. Synthetic client-side projection tests cover UUID/email separation, current role and negative malformed data; the signed browser ADMIN E2E must remain green.

## IR003 Redis key privacy repair

All **new** JWT registration and blacklist Redis keys use deterministic SHA-256 digest identifiers, with the original signed JWT never placed in the key name; existing positive expiry bounded by signed JWT `exp` remains unchanged. The code supports read-only fallback for legacy raw JWT keys to avoid silently invalidating already issued refresh credentials, and explicit logout deletes the identified credential in either supported format. No bulk migration, scan, deletion or mutation of historical retained keys is authorized; a future isolated operational cleanup requires a separate Product disposition. Synthetic unit and disposable HTTP/Redis tests prove opaque new keys, TTL, legacy lookup and logout compatibility. This is not a claim that all historical Redis storage risk has been eliminated.

## IR004 F001 — single validated TanStack Query factory

The shared React identity cache key must be paired with one shared **validated query function**. Both `AuthProvider` and `useAdminIdentity` now consume `verifiedAuthIdentityQuery(token, sessionGeneration)`. This factory checks the untrusted JWT for UX only, performs exactly one authenticated `/auth/me` request and passes the server response through `projectServerAuthUser` (same subject ID, authoritative email/current role, active account). ADMIN must never reuse raw API response data under the validated profile cache key. The real backend remains responsible for JWT signature and authorization. No Product acceptance is implied until CI and new independent review on the successor tree.

## A03 — signed per-login session revocation (proposed in successor)

Each new login emits an access+refresh JWT pair containing one cryptographically signed UUID4 `sid`. Refresh preserves that `sid`; both authorization pipelines check Redis for the hashed session revocation marker and individual token blacklist, failing closed with HTTP 503 when Redis is unavailable. Logout requires a signed registered refresh; a still-valid bearer, if supplied, must match the refresh sub and sid, uses one Redis Lua operation to check registered refresh ownership, revoke the session, delete refresh registration, blacklist the token and write an opaque idempotent acknowledgement, and invalidates all already issued access JWTs of that session. A mismatched session cannot revoke another credential. Historical JWTs without `sid` remain eligible only until their original expiry and subject-wide Redis revocation: legacy logout writes an opaque per-subject TTL marker and invalidates all other SID-less bearer and refresh credentials for that subject, including independently minted legacy tokens. New SID-bearing sessions from that subject remain independently valid. This is intentionally wider than individual old-token blacklisting because legacy JWTs have no signed family identifier. No retained Redis keys are scanned, deleted in bulk or migrated. The SPA holds refresh in tab-scoped sessionStorage and clears local state even if remote logout fails, reporting revocation as unconfirmed rather than claiming success. This is a candidate security contract subject to synthetic PG15/Redis7 and browser E2E plus independent full review; no Product acceptance or deployment is implied.

## IR006 — tab-scoped credential consistency

Both access and refresh tokens now live in the same tab-scoped `sessionStorage`, not a mixed persistent/local arrangement. Old access-only `localStorage` entries are discarded on app boot and require a fresh sign-in, without copying or migrating historical tokens. Same-tab reload retains both; a different tab cannot inherit an access token without its revocable refresh. The browser remains vulnerable to an XSS with access to JavaScript storage; this is not equivalent to a HttpOnly-cookie architecture. Exact signed ADMIN/client browser E2E must demonstrate same-tab persistence, absence of persistent access, remote logout revocation and stale-401 races. No real retained Redis/DB state was accessed or changed.


## A03 — revocación con access JWT expirado (candidato, pendiente de IR)

El endpoint `POST /auth/logout` autentica la revocación a partir del refresh JWT firmado, de propósito correcto, no invalidado y **registrado en Redis**. Un access token vencido o ausente ya no impide revocar el `sid` firmado de ese refresh; un bearer todavía válido que pertenezca a otra cuenta/sesión continúa rechazado con HTTP 403. El servidor aplica una operación Redis Lua única: verifica el refresh registrado y su sujeto, revoca la familia o el bearer legacy y registra un ACK opaco para reintentos idénticos. Las peticiones no registradas devuelven 401, los refresh malformados 400 y un Redis no disponible 503. Los tokens legados sin `sid` revocan, en la misma operación Lua, todos los JWT legacy del mismo sujeto firmado mediante una marca temporal de sujeto con hash opaco; no afecta sesiones modernas con `sid`. No se realiza migración, scan ni modificación masiva de históricos retenidos. El ADMIN frontend captura las excepciones de logout automático y muestra advertencia de revocación no confirmada, sin reactivar sesión local. Pruebas HTTP reales con DB/Redis descartables verifican la transición.

## Control 012 — Redis logout confirmation and bounded SPA retry (candidate)

Only a signed refresh JWT with matching issuer purpose, a valid original expiry
and the current registered subject may authorize logout. A still-valid access
bearer, if provided, must match the refresh subject and signed session. One
Redis Lua operation handles the registration check and writes, including
legacy raw-key compatibility, an expiry-bounded session tombstone and opaque
SHA256-keyed logout confirmation. A repeated signed refresh may yield 204 only
when its exact previous confirmation is found. Never registered: 401.
Redis outage, script failure or unknown acknowledgement: 503 / UNCONFIRMED.
Redis script execution is isolated from concurrent commands, but does not
magically roll back earlier writes if a runtime error occurs inside the script.

The SPA still removes both tab-scoped credentials immediately on logout
and never restores authenticated UI state from a remote failure. For network
acknowledgement loss or transient HTTP 429/502/503/504, the same operation
attempts exactly one additional POST with the in-flight, in-memory credentials.
If the second attempt fails, the error propagates to the existing UI warning.
No bearer is copied into localStorage or retained for later page reload; a
failed remote logout can remain unconfirmed until signed token expiration.
This residual risk is explicit, not automatically accepted by CI or Control.

The auth-service user resolver now requires the FastAPI-injected managed
database session. It no longer advances an unmanaged async session generator.
This document describes a candidate only, not a Product acceptance or merge.

## Control 012 — residuales y calificación negativa (candidato)

La revocación Redis sobre recursos descartables distingue: ejecución real
confirmada cuyo ACK de transporte se pierde y se recupera mediante un
reintento idempotente; script de fallo sintético inyectado tras la primera
tombstone SID, que NO revierte escrituras previas y responde 503 sin ACK;
y dos access legados sin SID, revocados ahora ambos mediante el marcador
opaco de sujeto que se consulta en todos los guards backend. Otro refresh
legacy del mismo sujeto también queda denegado; una sesión con SID queda válida.
La marca tiene TTL acotada al máximo intervalo legado más margen de reloj.

Dos fallos de red consecutivos o recarga antes del ACK dejan el logout
remoto UNCONFIRMED; no se persisten JWT para reintentos posteriores.
El residual de red UNCONFIRMED requiere aceptación explícita del Developer para
promover PR #107, y no se convierten en 0 advisories por CI positiva.
El alias trainer es histórico de presentación; la navegación protegida
solo puede utilizar los roles canónicos persistidos del backend.

## Control 012 — aviso no secreto para revocación remota no confirmada

Ante logout, la UI descarta acceso y refresh de sessionStorage de inmediato.
Antes de intentar la revocación remota registra únicamente la bandera no
secreta fitflow_logout_remote_unconfirmed=1, que no tiene credenciales ni
autoriza operaciones. Solo una revocación HTTP 204 confirmada la elimina.
Si ambas peticiones fallan, el aviso sigue visible tras recargar la misma
pestaña en la pantalla de login. El usuario puede ocultarlo explícitamente,
pero eso **no revoca** el servidor ni produce un ACK de revocación.
Un nuevo inicio de sesión tampoco confirma la revocación de la anterior.

Esta mejora no promete revocación durante una partición completa de red:
si la solicitud nunca llega al backend, una credencial remota puede sobrevivir
hasta su expiración firmada. El estado continúa UNCONFIRMED; aceptar esa
limitación Product requiere una decisión específica del Developer.

## Control 012 — confirmación HTTP estricta y avisos de solicitudes concurrentes

El cliente requiere explícitamente HTTP **204** para considerar confirmado
un logout remoto. Aunque Axios resuelva otras respuestas 2xx (200/202),
esas respuestas NO constituyen ACK de revocación y se informa UNCONFIRMED.

Cuando comienzan varios logouts, la pestaña mantiene una lista de identificadores
**no secretos** de cada solicitud pendiente en sessionStorage, además del aviso
global no secreto. Un ACK 204 elimina únicamente el identificador de la
solicitud a la que corresponde. Un ACK tardío de la sesión A no puede
borrar la incertidumbre de la sesión B, ni una sesión nueva confirmada
borrar la incertidumbre histórica previa. Los identificadores no contienen
JWT, hash de JWT, email, rol ni datos de usuario y no otorgan autoridad.

La acción de ocultar la advertencia solo afecta el estado de presentación
durante esa renderización; NO elimina el registro local de intentos
pendientes ni los convierte en confirmados. Tras recargar reaparece
cualquier advertencia todavía pendiente. El formulario de login elimina
su contraseña del estado React inmediatamente después de emitir la
mutación, sin persistirla en almacenamiento.

Estas medidas hacen auditable la incertidumbre local, pero no pueden
revocar una sesión remota si ninguna petición alcanza el servidor.

## Control 012 — rechazo Developer de limitaciones del logout (gate NO_ACCEPTED)

El Developer NO acepta como resultado final las limitaciones de logout
remoto UNCONFIRMED, invalidación legacy por cuenta sin familia delimitada
ni errores Lua que pueden escribir tombstones antes de devolver 503.
Los tests del candidato observan correctamente esos casos, pero esas
observaciones NO constituyen una aceptación de las limitaciones.

La solución final deberá presentar un protocolo de revocación
autoritativo del servidor y probar, con dos sesiones aisladas y fallos
descartables, que: (1) todo ACK HTTP 204 es verificablemente idempotente,
(2) las rutas protegidas y refresh rechazan sesiones revocadas incluso
después de reiniciar los componentes permitidos por el contrato de
durabilidad, (3) el modo legacy no afecta credenciales fuera de la familia
autorizada, (4) cualquier fallo parcial se refleja como pendiente sin
hacer promesas falsas, y (5) existe recuperación comprobable de
solicitudes pendientes tras cortes y reanudación del cliente.

Restricción física de diseño: cuando el cliente no puede transmitir
la intención al servidor, ningún protocolo puede garantizar que el
servidor ya revocó el token. Por eso **no** se permite declarar
logout completo en ese estado. Si el Product exige revocación inmediata
incluso con conectividad totalmente ausente, ese requisito no es
satisfacible mediante una PWA/JWT remota y requiere reformular el
contrato de operación; no se puede enmascarar con UX o TTL.

Como avance acotado no aceptado, el frontend limita a 24 IDs no
secretos los intentos pendientes y conserva un marcador de
incertidumbre no eliminable por ACK ajenos cuando se compactan IDs.
Errores de Storage se tratan con un aviso restrictivo solo en memoria;
si el navegador impide persistir datos, la persistencia tras cerrar
la pestaña NO queda garantizada ni se declara como tal. Las pruebas
descartables deben diferenciar esa incertidumbre de una revocación
confirmada por backend. Ninguna de estas reparaciones autoriza merge,
aceptación 0/0, despliegue o cierre de Issue #108.

