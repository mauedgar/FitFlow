# Operacion IA vNext

`config/` define Project Profile, policies y registries; `contracts/v2/` valida
intercambio; `templates/` materializa vistas; `tasks/` conserva contratos de
trabajo; `runs/` conserva evidencia estructurada durable.

AI Core vive en `../FitFlow-ai` y consume estos archivos mediante ports. El
adapter OpenCode no puede reducir gates ni introducir secretos.

Todo run nuevo usa v2. Los schemas v1 permanecen para historial.
