# Configuracion activa

Los archivos de este directorio constituyen la configuracion activa de baseline
vNext. `models.yaml` y `roles.yaml` requieren sus schemas v3 estrictos; entradas
v2 son unsupported. `finops.yaml` conserva v1 con paid API deshabilitada.

`project-profile.yaml` contiene decisiones especificas de FitFlow. AI Core debe
leer ese perfil mediante un adapter y no duplicar sus valores en codigo.

## Ownership y ubicaciones

- FitFlow es propietario de `project-profile.yaml` y de los registries activos
  de este directorio.
- Tecnotron-ai es propietario del AI Core identificado por `roots.ai_core` y del
  entorno reutilizable de discovery declarado en
  `environment.reusable_discovery_env`. Ese entorno no es el entorno oficial;
  `environment.official_ai_core_env` permanece `null`.
- El Developer conserva la autoridad terminal. `roles.yaml` y
  `orchestrator.yaml` materializan esa autoridad sin transferirla al AI Core.
- El Project Profile activo vive en `.ai/config/project-profile.yaml` bajo el
  root de producto declarado. Sus ubicaciones operativas de runs y estado local
  se declaran en `operational`.

Los roots fisicos describen los checkouts principales. Worktrees coordinados
reciben `FF_PROJECT_ROOT`, `FF_AI_CORE_ROOT` y `FF_PROJECT_PROFILE` desde el
entorno de ejecucion; esa inyeccion pertenece al workspace y sus paths
temporales no se persisten en esta configuracion.

## Inyeccion en worktrees Orca

`orca.yaml` conserva `defaultTabs[].command` y la pestaña visible `AI Core`,
pero sus comandos automaticos solo muestran instrucciones. No inyectan roots
historicos, no leen ni copian `.env`, no instalan dependencias ni inician Docker,
agentes o modelos. El runtime Windows/WSL se selecciona explicitamente en Orca.

Antes de ejecutar AI Core, la tarea autorizada debe recibir `FF_PROJECT_ROOT`,
`FF_PROJECT_PROFILE` y `FF_AI_CORE_ROOT` desde el binding de estacion vigente.
Los valores deben identificar los checkouts y el Profile competentes; no se
deducen de directorios hermanos ni se heredan de una ruta historica sin verificar.
Este cambio de hooks no migra los roots del Project Profile versionado.

Usar `--setup skip` cuando la tarea no autorice preparacion. Las dependencias
se preparan por decision explicita, con `node_modules` y entornos virtuales
aislados por worktree y sistema operativo. Se puede reutilizar la cache npm
nativa del usuario, no directorios de dependencias Windows/WSL ni `.venv`.
La politica local de Orca debe omitir setup indiscriminado y esperar su
finalizacion antes de iniciar un agente cuando se autorice preparacion.

Los estados `accepted_pending_*`, `reported_*`, `untested` y `null` son
deliberados: describen capacidades no verificadas sin promoverlas a operativas.

## Legacy baseline compatibility field

`project-profile.yaml` and `orchestrator.yaml` still carry
`baseline: fitflow-ai/vnext-5.0` because the currently integrated strict
schemas require a string `baseline` field. That value is a compatibility token,
not the current canonical process baseline and not a source of authority.
No replacement identifier is inferred until a competent decision establishes
one.
