---
document_id: FF-PY315-MIGRATION-DOCIMPACT-20261104-001
status: draft_review_incomplete
date: 2026-11-04
product_acceptance: not_granted
source: mauedgar/FitFlow
---

# FitFlow — Python 3.15.2, candidato aislado

## Proveniencia

Fuente inicial PR #82 `4be0b32822a5cd2272db96b6402853804ef089b1`, tree `181e65f69584754f74708cf324b2876ccd87902c`. `develop@55772398c72f4c1a41862dccd79b04d38016dfcb`, SOT v5.3 blob `f36307af0777fd3b493792ad42115fec56ac44b3`. Issue #44 DoD y autorización: https://github.com/mauedgar/FitFlow/issues/44#issuecomment-6621650094.

## Write-set

`pyproject.toml`, `.python-version`, `uv.lock` y exports derivados, Dockerfiles runtime/test, CI Python relevante, ADR 0020 y este DocImpact. La rama de migración es independiente de PR #82 original; se conserva auth bcrypt nativo y la historia de revisiones. El bootstrap de uv opera **solo** sobre una rama de migración e intenta generar el lock y exports por uv, con guardas de identidad. No modifica `develop`.

## Gates

- G1: CPython3.15.2 exacto y fuente única en el candidato: **PASS EN CANDIDATO**, no adoptado todavía en `develop`.
- G2: **PASS** para generación por uv e instalación de dependencias en CPython3.15.2: [run 41768133911](https://github.com/mauedgar/FitFlow/actions/runs/41768133911), base de generación `58d8249ac652966be106f3fee36fe9dcd3a73c4a`, commit generado `5a58bc868b4f38ad9930057511e12c2069ec30fc`, árbol `f0993eed448ae438f6583fda168c7d7bbbc53a9c`. Solo se alteraron `uv.lock`, `backend/requirements_backend.txt` y `backend/requirements_test.txt` mediante uv. Lock/export nuevos siguen sujetos a la CI/IR del candidato compuesto. No editar hashes manualmente. Si el bootstrap falla, preservar FAILED y diagnosticar, no repetir.
- G3: **PASS observado exclusivamente en `bc333139963501544eaee3257df8f4dc1f8e3eff` / tree `acf988991e50f0448ff97466f47e98bd07c261b8`**: suite completa PG15/Redis7/Alembic con 400 PASS y Ruff/Pyright 0 mediante [41772221738](https://github.com/mauedgar/FitFlow/actions/runs/41772221738); bcrypt 43 PASS/legacy y frontend mediante [41772221785](https://github.com/mauedgar/FitFlow/actions/runs/41772221785), schema [41772221659](https://github.com/mauedgar/FitFlow/actions/runs/41772221659), ingress descartable [41772221672](https://github.com/mauedgar/FitFlow/actions/runs/41772221672), baseline classifier [41772221756](https://github.com/mauedgar/FitFlow/actions/runs/41772221756). El classifier omite backend/frontend al ser DRAFT; no atribuirle dichos tests. Ningún PASS se transfiere automáticamente a un commit documental posterior.
- G4: Chrome E2E sintético montado con teardown y deadline acotados: **PASS observado exclusivamente en `bc333139...`**, [41772221812](https://github.com/mauedgar/FitFlow/actions/runs/41772221812). El intento PR82 [41763004024](https://github.com/mauedgar/FitFlow/actions/runs/41763004024) quedó CANCELLED y no se repitió. No es prueba de staging público.
- G5: [IR001 independiente](https://github.com/mauedgar/FitFlow/pull/83#issuecomment-6622519876): **COMPLETED / NO_RECOMMEND / REVIEW_INCOMPLETE** sobre `bc333139...`. Sin defecto confirmado en muestra; NO equivale a 0 findings en 204 paths. Requiere cobertura independiente y evidencia de árbol/lock/export; aceptación y merge **NOT_GRANTED**.
- G6: CI postmerge y reconciliación Issue #44/otros: **NOT_RUN**.

A10 (ACK externos), A12 (infra TLS/IP), A13 (Redis retenido) siguen abiertos; no son eximidos por esta migración ni por pruebas sintéticas.

## Reconciliación de intentos de resolución

- [41767614256](https://github.com/mauedgar/FitFlow/actions/runs/41767614256) FAILED inicial al resolver `HEAD^` en checkout superficial: corregido mediante `fetch-depth: 0` y verificación de ancestralidad. No se relanzó.
- [41767760202](https://github.com/mauedgar/FitFlow/actions/runs/41767760202) FAILED al instalar Pydantic 2.11.10 / pydantic-core 2.33.2: PyO3 0.24.1 solo admite hasta 3.13, incompatibilidad real de Python3.15. No se eludió guard de PyO3.
- [41768017083](https://github.com/mauedgar/FitFlow/actions/runs/41768017083) FAILED resolución: Pydantic>=2.14.2 necesita typing-inspection>=0.4.4 y fuente fijaba 0.4.1.
- [41768133911](https://github.com/mauedgar/FitFlow/actions/runs/41768133911) SUCCESS original: uv regeneró lock y exports, instaló CPython3.15.2, comprobó imports y dependencias; publicación de un commit derivado verificada en GitHub. No se repitieron intentos terminales.

## Reparación exacta posterior de Python 3.15.2

- En PR #83 el primer CI exacto [41768605881](https://github.com/mauedgar/FitFlow/actions/runs/41768605881) exhibió la falta de `psycopg` en Alembic, y [su job quality](https://github.com/mauedgar/FitFlow/actions/runs/41768605881) detectó 16 diagnósticos Ruff por objetivo Python3.15. No se ignoraron reglas ni se usó un target-version falso.
- Se agregó `psycopg[binary]==3.3.6` (wheel CPython3.15), se actualizaron dos clases genéricas a PEP695, anotaciones forward-ref tipadas y AsyncGenerator; sus pruebas exactas aún deben calificar el nuevo sujeto.
- [Run de generación de lock 41769298850](https://github.com/mauedgar/FitFlow/actions/runs/41769298850) SUCCESS en fuente `65b4cc061f7111525d12d33b27bad4cc9becda25`: uv publicó `8a5e0db7ba3cb3d414c7043330fe0d6d5ca79202` / tree `0992b606dcda05a7af01c011f1999fa00e05d730`, **solo** `uv.lock`, requirements runtime y requirements test. Lock incluye Pydantic 2.14.2, pydantic-core 2.50.2, psycopg/psycopg-binary 3.3.6, SQLAlchemy y asyncpg compatibles. No hay hashes manuales.
- Los workflows del commit intermedio `65b4cc...` anteriores a la regeneración terminaron con FAIL por `uv lock --check` o backend desechable todavía no calificado; no son evidencia contra el lock regenerado ni PASS transferible.
- El workflow temporal `.github/workflows/python315-lock-bootstrap.yml`, con permiso `contents: write` exclusivamente en la rama de migración, **se excluye del candidato final** para no mantener un emisor privilegiado sin necesidad. Su historial y resultados quedan trazables; la generación futura corresponde a workflow/Product autorizado separado.
- Nota histórica: al producir el commit intermedio de lock estas validaciones eran NOT_RUN. Estado posterior del candidato `bc333139...` descrito en la tabla de Gates anterior; IR001 no recomienda aceptación.

## Reparación posterior a CI 374eebb3

En [PR83 CI Issue52 41769819316](https://github.com/mauedgar/FitFlow/actions/runs/41769819316) la suite de CPython 3.15.2 completó 398 PASS / 2 FAIL: `inspect.get_annotations` con PEP649 intentó evaluar `Client` de una relación SQLAlchemy importada solo bajo `TYPE_CHECKING`; el test de superficie de usuarios dependía de un prefijo mutable, aunque la comprobación positiva de HTTP de registro pasó. Se añade `from __future__ import annotations` a siete modelos con forward refs para preservar evaluación diferida sin silenciar Ruff y se hace que el test verifique el path real de registro y la ausencia de PUT/PATCH de usuarios sin depender del prefijo de configuración mutable.

En [Issue43 bcrypt CI 41769819384](https://github.com/mauedgar/FitFlow/actions/runs/41769819384) las pruebas de compatibilidad histórica/quality/frontend fueron SUCCESS; un test de rutas de usuarios dio el mismo FAIL y recibe la misma corrección, no un waiver.

En [schema CI 41769819336](https://github.com/mauedgar/FitFlow/actions/runs/41769819336) la instalación de requirements generados para 3.15.2 falló porque el workflow todavía elegía 3.11.17. Se alinea ese workflow a 3.15.2 sin cambiar el esquema ni el DB real.

Los otros workflows del candidato 374eebb3 fueron SUCCESS: browser montado, ingress Nginx/PG/Redis desechable, frontend/quality y baseline. Esos PASS históricos siguen vinculados a ese SHA, sin transferencia al nuevo candidato.

**Estado histórico de `374eebb3` solamente:** las validaciones posteriores constan en Gates. La aceptación/integración aún no fue concedida; A10/A12/A13 siguen abiertos.

## Rutas de usuarios: reconciliación exacta de 24dcc421

El nuevo SHA 24dcc4212f8c49ee320c9ee726a0c05727f0331a conserva las pruebas de registro HTTP positivas (201/422), ORM con anotaciones diferidas (sin NameError), Ruff/Pyright, schema, Chrome e ingress PASS. Las CI [Issue52 41770281387](https://github.com/mauedgar/FitFlow/actions/runs/41770281387) y [Issue43 41770281397](https://github.com/mauedgar/FitFlow/actions/runs/41770281397) fallaron en **la misma aserción aislada** de enumeración `app.routes` (399 PASS/1 FAIL y 42 PASS/1 FAIL). Se delimita la inspección negativa PUT/PATCH a `user_router.router.routes`, incluyendo comprobación positiva `POST /users/register`; los tests de registro HTTP del mismo archivo siguen demostrando el montaje y respuesta real. No se omiten pruebas ni reglas y no se modifica código Product de auth. Este antecedente fue calificado en el commit posterior `bc333139...` con seis CI exitosas, seguido de IR001 independiente incompleta.

## IR001 y disposición de cobertura

El receipt independiente [FITFLOW-PY315-IR001](https://github.com/mauedgar/FitFlow/pull/83#issuecomment-6622519876) sobre `bc333139963501544eaee3257df8f4dc1f8e3eff` / tree `acf988991e50f0448ff97466f47e98bd07c261b8` tiene disposición **NO_RECOMMEND por REVIEW_INCOMPLETE**, no por un fallo de código demostrado. Confirmó 204 paths (146 modificados, 58 agregados; ninguno eliminado) y SOT v5.3, sin verificar árbol ni revisar íntegramente todas las diferencias. IR001-A14 (estado documental desactualizado) se repara con el presente cambio de DocImpact, que es **documental exclusivamente**; verificar identidad del commit sucesor y equivalencia exacta de todos los blobs Product antes de reutilizar una conclusión de riesgo, nunca transferir PASS sin reconciliación.

Para completar IR001-A01, revisión independiente distribuida por superficies del **mismo** SHA/tree: (1) Python/uv/CI/migraciones/entorno, (2) auth/JWT/Redis/privacidad/seguridad HTTP, (3) dominio/modelos/services/tests y (4) frontend/Chrome/UX/documentación/contratos. Un control independiente debe comprobar cobertura disjunta y completa del diff, objetos Git exactos, lock + exports con hashes originados por uv y eventuales hallazgos cruzados. Esta partición es solo método de validación, no nuevo TaskCycle ni aceptación.

A10 (ACK externo y rollout), A12 (infra TLS/IP host real) y A13 (Redis retenido y privacidad) siguen pendientes de evidencia real. No deben eliminarse ni recatalogarse como 0 advisories por CI sintética. El merge a `develop`, cualquier rollout y cierre Issue44 siguen sujetos a decisión Product competente, SOT y revisión conclusiva.

## IR002-P/D targeted repair following independent review (2026-11-04)

- [IR002-P partial](https://github.com/mauedgar/FitFlow/pull/83#issuecomment-6622649792) A-P01 flagged mutable Python and uv base image tags. The original disposable build [41773482177](https://github.com/mauedgar/FitFlow/actions/runs/41773482177) resolved `python:3.15.2-slim-bookworm@sha256:4e03260adeeebafccd084f3584e6b84823aba5651cfb53ef8a078ed441ddf9cd` and `ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0`. Candidate Dockerfiles now pin exactly those observed manifests; new Docker build on current candidate required. No cross-architecture guarantee.
- [IR002-D partial](https://github.com/mauedgar/FitFlow/pull/83#issuecomment-6622756345): A-D01 transaction ownership is bounded in active booking route and front-desk caller (both close existing read transaction before atomic CRUD). Concurrency row-lock and HTTP transaction boundary tests exist; do not declare migration acceptance from this alone. A-D02 an unused pure duplicate helper wrongly treated cancelled history as active; reconcile it with the atomic CRUD, adding positive/negative unit tests. A-D03 `get_client_weekly_activity` counts a rolling future 7 days in UTC; clarify its docstring, no Product behavior change or user timezone policy change.
- Original 6/6 CI on `d6002a39762addf898e57d1457779f6131042f45` belongs only to that SHA/tree. Any new commit needs its own exact CI and qualified Independent Review. A10/A12/A13 remain OPEN for real rollout. IR002-S/T/F are not yet comprehensively reviewed; do not claim global 0 findings.

## IR003 — reparación CI y E2E posterior al candidato 72db1229 (2026-11-04)

El sujeto `72db1229e5d0c3b0d456321c3a7cce1149ca66bc`, tree `7a0939c6970d5d54701822358186cf5929514da0`, obtuvo **6/6 CI originales SUCCESS**: backend Python3.15.2 **405 PASS**, Ruff/Pyright sin diagnósticos, bcrypt43 y compatibilidad heredada, frontend, Chrome sintético, schema y Nginx/PG/Redis efímeros. No inferir PASS de los jobs baseline backend/frontend omitidos por política DRAFT anterior.

Las revisiones separadas de ámbito P1 y T identificaron **4 findings concretos (P1-F01/F02 y T-F01/F02)**: workflow baseline podía mostrar éxito de clasificador sin ejecutar suites en PR DRAFT; Issue52 repetía suite backend completa; prueba de ausencia de PUT/PATCH dejó de verificar la aplicación realmente montada; Chrome no esperaba el cierre confirmado de procesos ni del directorio temporal. La presente reparación cambia exclusivamente workflow/test/harness y no reglas Product:

- `.github/workflows/fitflow-baseline-ci.yml`: los PR DRAFT también clasifican y ejecutan sus suites necesarias; nuevo job `qualification` con `if: always()` falla si scope falla, si una suite requerida se omite/falla o si una suite no requerida ejecuta inesperadamente. Un solo full backend bajo la matriz Product Python3.15.2.
- `.github/workflows/issue52-ir001-repair-verify.yml`: preservar check de lock/PG/Alembic/Ruff/Pyright y sustituir full pytest por regresiones focalizadas HTTP de registro, privacidad y perfil. El test integral reside en baseline.
- `.github/workflows/deterministic-ci.yml`: requerir `expected_tree` válido de 40 hex en el dispatch y compararlo con `HEAD^{tree}` antes de ejecutar o producir receipt. No cambia la semántica de receipts históricos ya emitidos.
- `.github/workflows/fitflow-ci.yml`: retirar workflow dormido solo `main/dev` con instalación flotante de `openai` y credencial externa; no forma parte de `develop`/baseline y no constituye gate Product.
- `backend/tests/api/test_auth_registration_password_boundary.py`: preservar los HTTP positivos 201/422, verificar registro POST tanto declarado como montado, y rechazar PUT/PATCH tanto en router fuente como en superficie FastAPI montada, sin depender del prefijo mutable de fixtures.
- `frontend/tests/browser/fitflow-mounted-e2e.cjs`: cerrar hijos por `SIGTERM` y esperar `close`, escalar a SIGKILL con deadline, cerrar API mock y verificar la eliminación del perfil temporal antes de terminar. El watchdog intenta limpieza incluso en deadline 180s; timeout externo 240s se conserva.

Disposiciones de alcance de las revisiones anteriores: dominio D1 6/6 PASS_SEGMENT, D2 6/6 PARTIAL; P2 (lock/Docker) 8/8 PARTIAL sin finding bloqueante, O (docs/legacy) 10/10 PARTIAL. Sus conclusiones se vinculan exclusivamente a `72db1229...`, no califican el nuevo commit generado por estas reparaciones ni sustituyen una IR integral.

**Limitaciones/no efectos:** Branch protection para `develop` no pudo auditarse (GitHub API responde 403); rulesets públicos consultados no exponen reglas. El nuevo check `Required scope disposition` debe ser requerido por la política competente antes de merge. Hosted Dependabot uv [41826411939](https://github.com/mauedgar/FitFlow/actions/runs/41826411939) corrigió lectura UTF-8, abrió PR84–88 y reportó 11 conflictos de constraints; ver [receipt único Issue44](https://github.com/mauedgar/FitFlow/issues/44#issuecomment-6633979808). No integrar locks bot del baseline anterior sobre el lock Python3.15. El archivo `frontend/requirements_frontend.txt` contiene dependencias Python heredadas, sin consumidor runtime verificado; conservarlo hasta una disposición separada sobre descubrimiento Dependabot, no darle autoridad canónica.

**Nuevo estado:** candidato de reparación PREPARADO, CI exacta/IR de nuevo SHA **NOT_RUN**. A10 (ACK externos), A12 (staging TLS/IP real), A13 (Redis histórico/retención) **OPEN**; no release ni despliegue ni integración sin evidencia Product pertinente.

### IR003 repair follow-up: HTTP 405 proof on candidate efb48c3 (2026-11-04)

GitHub Actions originales exactos sobre `efb48c3da5e5f099cd4a017666a7e27bbe6267f5`: [41856121555](https://github.com/mauedgar/FitFlow/actions/runs/41856121555) schema SUCCESS, [41856121834](https://github.com/mauedgar/FitFlow/actions/runs/41856121834) Chrome E2E con cleanup SUCCESS, [41856121725](https://github.com/mauedgar/FitFlow/actions/runs/41856121725) ingress descartable SUCCESS; los tres workflows backend [41856121731](https://github.com/mauedgar/FitFlow/actions/runs/41856121731), [41856121454](https://github.com/mauedgar/FitFlow/actions/runs/41856121454) y [41856121341](https://github.com/mauedgar/FitFlow/actions/runs/41856121341) terminaron FAILURE por **la misma aserción** de introspección del singleton FastAPI `app.routes`. Full regression: 404 PASS / 1 FAIL; bcrypt: 42 PASS / 1 FAIL; Issue52 focalizado: 90 PASS / 1 FAIL. El nuevo job `Required scope disposition` cerró correctamente en FAILURE al fallar backend, demostrando el control de no falso PASS.

El siguiente candidato conserva los tests positivos reales de registro 201/422 y la inspección de PUT/PATCH del router fuente, pero reemplaza la enumeración global de `app.routes` por **seis probes HTTP reales**: PUT/PATCH contra `/users/register`, `/users/me`, `/users/public`, con HTTP 405 obligatorio y 404 inequívocamente fallido. Esto prueba la ruta montada sin depender de un singleton alterado por otros fixtures. No se modifica el código Product de auth ni los modelos. CI e IR exactas del nuevo commit: PENDIENTES hasta publicarse/ejecutarse; no relanzar runs terminales previos.

El token de acceso a reglas de protección `develop` responde 403; hay que exigir que `Required scope disposition` sea required check en la configuración competente antes de integrar. La configuración de permisos no se ha cambiado. A10, A12, A13 y la resolución alojada Dependabot uv siguen como dependencias separadas.

### IR004-T residual cleanup advisories — next bounded candidate (2026-11-04)

- Original current baseline before this adjustment: `cd972511be808319df50340d8b5cb48ca1f1d291` / tree `dee83ebb626ad7c3e45ad11fac9c0176b491e276`. Six native workflows attempt1 SUCCESS: baseline 41856870287 with 405 backend PASS and Required scope disposition PASS; Issue52 41856869880 with 91 focused PASS; Issue43 41856869883 with 43 PASS; Chrome 41856870013 with E2E_BROWSER_CLEANUP_PASS; schema 41856870159 and disposable ingress 41856870283 PASS. These outcomes **do not transfer** to the new commit.
- Independent IR004-P finished PASS_SEGMENT on four CI paths, no confirmed findings and two LOW advisories: branch-protection required-check (GitHub endpoint 403; cannot confirm), and manual deterministic workflow callers now requiring `expected_tree`. Independent IR004-T was PARTIAL, no confirmed functional finding, two browser teardown advisories: A-T01 an `error` event was incorrectly accepted as a child `close`; A-T02 WebDriver DELETE failure was only logged but could still yield `E2E_BROWSER_CLEANUP_PASS`. These are repaired narrowly in `frontend/tests/browser/fitflow-mounted-e2e.cjs` by awaiting actual close (or bounded failure) and marking DELETE failure as a cleanup failure. New exact CI + independent reviewer still required.
- The separate-context IR004 results are task outputs, **not GitHub-published IR receipts**. A previous request to publish an additional IR comment was blocked by platform safeguards; do not retry or route around that effect. Formal published IR is still outstanding; no acceptance or integration.
- External A10/A12/A13 operational security dependencies, real retained Redis and host staging, plus Issue44 Dependabot resolver conflicts remain outside this browser-only fix. Product develop and SOT untouched.
