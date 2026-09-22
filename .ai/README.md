# Operacion IA vNext

`config/` define Project Profile, policies y registries; `contracts/v2/` valida
intercambio; `templates/` materializa vistas; `tasks/` conserva contratos de
trabajo; `runs/` conserva evidencia estructurada durable.

El sistema de desarrollo externo es Tecnotron-ai. Su root se resuelve desde
`.ai/config/project-profile.yaml` o una referencia explicita compatible; no se
infiere por nombre de directorio hermano. El adapter OpenCode no puede reducir
gates ni introducir secretos.

Todo run nuevo usa v2. Los schemas v1 permanecen para historial.
