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

`orca.yaml` usa la superficie soportada `defaultTabs[].command`. La pestaña
`AI Core` toma su checkout de FitFlow desde el directorio inicial de la terminal,
deriva de este el Profile activo e inyecta el checkout `tools` de Tecnotron-ai.
No consulta topologia de directorios hermanos ni lee `.env` para resolver estos
valores. En una ejecucion coordinada, `FF_AI_CORE_ROOT` debe identificar el
checkout de Tecnotron-ai autorizado por el Developer.

Para un smoke sin secretos ni instalacion de dependencias, el worktree se crea
con `--setup skip`, que evita ejecutar el setup de producto y conserva su
lifecycle independiente. Si la politica local de Orca no autoejecuta comandos
versionados, `orca worktree create` aun materializa el `defaultTab` y la terminal
se inicia por la superficie soportada `orca terminal create --title "AI Core"
--command <defaultTabs[0].command>`. La validacion comprueba solo presencia y
coherencia de paths; la politica local no se cambia ni se convierte en
configuracion global.

Los estados `accepted_pending_*`, `reported_*`, `untested` y `null` son
deliberados: describen capacidades no verificadas sin promoverlas a operativas.
