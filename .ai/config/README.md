# Configuracion activa

Los archivos de este directorio constituyen la configuracion activa de baseline
vNext. `models.yaml` y `roles.yaml` requieren sus schemas v3 estrictos; entradas
v2 son unsupported. `finops.yaml` conserva v1 con paid API deshabilitada.

`project-profile.yaml` contiene decisiones especificas de FitFlow. AI Core debe
leer ese perfil mediante un adapter y no duplicar sus valores en codigo.

Los roots fisicos describen los checkouts principales. Worktrees coordinados
declaran `FF_PROJECT_ROOT`, `FF_AI_CORE_ROOT` y `FF_PROJECT_PROFILE`; esos paths
temporales no se persisten en esta configuracion.

Los estados `accepted_pending_*`, `reported_*`, `untested` y `null` son
deliberados: describen capacidades no verificadas sin promoverlas a operativas.
