---
document_id: FF-ISSUE36-BASELINE-CI-20261103-001
status: review_required
issue: 36
branch_baseline: develop
baseline_commit: daee5694fcf9ba301896200735c68ba8b55643ad
baseline_tree: 714def442ee62c55f1cd0c7c1a5fc03414f10fb0
sot_blob: f36307af0777fd3b493792ad42115fec56ac44b3
acceptance: false
---

# Issue #36 — Una CI básica y determinista para develop

## Alcance

Nuevo workflow aislado `.github/workflows/fitflow-baseline-ci.yml`.
No modifica los write-sets activos de PR #42
(`deterministic-ci.yml`, `frontend-regression.yml`) ni de PR #68
(backend/frontend de seguridad y workflows especializados). El
workflow antiguo `fitflow-ci.yml` continúa intacto y no se
ejecuta en `develop`; no hay secreto OpenAI ni LLM obligatorio.

La CI básica única opera por `pull_request` a `develop`
y `push` a `develop`, con `contents:read` y cancelación
solamente de ejecuciones anteriores del mismo PR/ref.
**Draft:** ejecuta únicamente el job liviano `scope` para
anotar `FITFLOW_NOT_RUN_DRAFT`; backend/frontend quedan
`NOT_RUN` hasta el evento `ready_for_review`. Esto
evita el ciclo pesado en cada commit provisional. Si el
PR ya es Ready, una nueva sincronización vuelve a
calificar el SHA nuevo, cancelando solamente el intento
anterior aún en vuelo. Selecciona
por el diff Git real entre base/merge-base y candidato exacto:
- backend/*, pyproject.toml, uv.lock y scripts/ci/* activan
  la suite completa backend **una vez** en Python 3.11.17
  con PostgreSQL15 y Redis7 descartables y migración Alembic;
- frontend/* activa tests Node, ESLint y build TypeScript
  desde package-lock y .nvmrc una vez;
- cambio del propio workflow o de otros workflows/código
  no reconocido activa ambas suites, por defecto seguro;
- docs/ y plantillas puras no ejecutan suites Product:
  resultado deliberado **NOT_RUN/N/A**, no PASS implícito.

El job de clasificación registra SHA y tree al calificar
un candidato listo. Para un Draft registra explícitamente
`NOT_RUN_DRAFT`, no hace checkout ni declara pruebas
`PASS`. Si `git diff` falla o la base no existe,
el job falla (no convierte un error en rutas vacías).
Cada job seleccionado verifica por separado el checkout
del SHA exacto del PR (no lo confunde con el synthetic
merge de GitHub), y publica el tree en logs. El workflow
en `push` verifica `github.sha` y el commit previo,
o activa ambas suites si la información de origen falta.

**Sin nuevas dependencias**; usa herramientas, tests y
contenedores descartables ya utilizados/validados por
los candidatos de CI previos, con checkout, setup-python,
setup-node y servicios Docker por referencias inmutables.
No Docker local; sólo servicios estándar de GitHub Actions.

## Razonamiento de coste y contratos no sustituidos

El backend no repite matrices Python3.11/3.12/3.13
por cada push de desarrollo; esa compatibilidad de
releases/seguridad sigue siendo un gate **distinto**,
obtenido por el dispatch SHA-pinned ya existente y
validadores especializados cuando corresponda.
Se mantiene inalterado `deterministic-ci.yml`.
No se reclama haber ejecutado Ruff/Pyright de Product:
el baseline en `develop` tiene todavía deuda #47;
tests/lint frontend se verifican según su alcance.

No confundir checks omitidos por clasificación con
PASS; el scope registrado debe acompañar a cualquier
decisión de aceptación. Los filtros de PR acumulativo
operan sobre TODO el diff frente a `develop`, no
solo el último commit. Cancelar in-flight superseded
no autoriza reintentos de efectos Product.

## Relaciones y límites

- PR #42 queda abierto hasta reconciliar/anotar la
  equivalencia con el nuevo flujo y su diferencia
  semántica. Su IR004 0F/3A no se hereda ni convierte
  en PASS y jamás se integra silenciosamente junto
  con este workflow.
- PR #68 y su IR017 permanecen intactos. Los tests
  especiales de bcrypt/Chrome/Nginx/schema seguirán
  corriendo en ese PR hasta resolver su propia
  autoridad, y no se consideran eliminados por esta
  propuesta de CI básica.
- A01 E2E real #25/#37, A06 reproducibilidad y A07
  Passlib pertenecen a sus gates reales; no declarar
  esos objetivos satisfechos por tests AST/HTTP
  sintéticos.
- Issue #36 no se cierra hasta verificar los checks
  sobre PR y posterior merge a `develop`, con
  evidencia vinculada al sujeto exacto y DoD.

## Validaciones exigidas antes de aceptación

Parseo YAML/eventos y casos negativos de selección:
solo docs, solo backend, solo frontend, workflow
cambiado, ruta desconocida, push con before ausente,
base/head equivocados, diff Git fallido y Draft
sin pruebas hasta `ready_for_review`. Validación real en Actions
sobre el candidato SHA/tree con PG/Redis, Node
tests/lint/build, sin secretos pagos, seguida de
una original Independent Review en contexto separado
sobre el mismo árbol. Sin integración ni cierre
automático por CI sola.


## IR001 A01 — matriz de pruebas negativas reproducibles

La revisión independiente original IR001 identificó A01 (evidencia insuficiente
de ramas negativas del clasificador) en el commit e8ef79c0. Esta reparación
NO traslada el resultado de esa revisión a un candidato nuevo.

Se incorpora scripts/ci/test_fitflow_baseline_scope.py (Python unittest estándar,
sin dependencias nuevas ni contenedores) y una ejecución previa al clasificador
de GitHub Actions en el job liviano de scope para PR Ready y push develop.
El test extrae exactamente el bloque Bash ejecutable del workflow en el
mismo checkout; si se cambia el bloque, la regresión prueba su nueva
implementación en vez de una copia simplificada.

La batería usa repositorios Git TEMPORALES y no se conecta a GitHub,
PostgreSQL, Redis o servicios externos. Prueba diez combinaciones
de rutas (docs/template/README, backend, frontend, scripts/ci,
workflow, combinación y desconocida) y siete casos de regresión:
borrado de backend, push con before válido, push sin before,
SHA incorrecto, base inválida y fallo real de git diff inyectado
con un shim de Git que delega todos los demás comandos. Los últimos
casos comprueban que NO se emitan outputs backend/frontend engañosos.

Preflight local con git y Python standard library: 7 métodos unittest
(ten scenarios de subTest + seis métodos restantes), PASS en
repositorios descartables. Ese PASS local no equivale a CI del nuevo SHA.
El scope CI debe publicar luego el resultado de los mismos tests y
mantener su propia comprobación de checkout SHA/tree. En Draft, ni
checkout ni tests se ejecutan: NOT_RUN_DRAFT preservado.

No se cambia la lógica Product, los tests backend/frontend, las
matrices especializadas, PR42/PR68, dependencias o secretos.
Solicitar una nueva IR independiente sobre el commit/tree exacto;
A01 sólo se considera resuelto si la CI y reviewer verifican la
matriz original, su output, límites y vinculación al sujeto.
