# Configuracion activa

Los archivos de este directorio constituyen la configuracion v2 de baseline
vNext. `schema_version` identifica cada contrato. La configuracion v1 se
conserva en Git y en artefactos historicos; no se mezcla dentro de un run v2.

`project-profile.yaml` contiene decisiones especificas de FitFlow. AI Core debe
leer ese perfil mediante un adapter y no duplicar sus valores en codigo.

Los roots fisicos actuales describen la configuracion del producto, pero no son
un mecanismo portable entre worktrees. Su resolucion desde Orca o el Project
Profile queda pendiente en `FF-AI-VNEXT-005`; no mover ni duplicar el perfil
antes de adaptar sus consumidores.

Los estados `accepted_pending_*`, `reported_*`, `untested` y `null` son
deliberados: describen capacidades no verificadas sin promoverlas a operativas.
