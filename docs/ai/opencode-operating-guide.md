---
document_id: FF-AI-OPENCODE-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Guía de operación con OpenCode

## Contrato de integración

OpenCode es la superficie de ejecución. Los nombres concretos de providers,
modelos, herramientas y archivos propios se resuelven en un adaptador. El
adaptador consume estos artefactos neutrales:

- `.ai/config/orchestrator.yaml`;
- `.ai/config/models.yaml`;
- `.ai/prompts/*.prompt.md`;
- `.ai/contracts/*.schema.json`;
- `.ai/tasks/<ID>/TASK.md`.

No duplicar reglas en configuración propietaria. Si OpenCode exige otro
formato, generarlo desde estos archivos y registrar versión/hash del adaptador.

## Entrada mínima de ejecución

```yaml
task_id: FF-000
stage: PLAN
scope: backend
risk: medium
baseline_revision: <git-sha-or-NO_COMMIT>
working_tree_fingerprint: <sha256>
ownership_keys:
  - path:backend/app/services/example.py
required_docs:
  - docs/architecture.md
  - docs/quality-and-validation.md
```

## Salida mínima

Cada subagente devuelve un bloque serializable con:

- `task_id`, `run_id`, `role`, `stage`;
- `status` y `next_state`;
- `evidence` con rutas/rangos/hash;
- `artifacts_written`;
- `validation` o `context_request` según corresponda;
- `model` y `reasoning_level` efectivos;
- `assumptions` explícitas, idealmente vacías.

## Reglas del adaptador

1. Validar input/output contra schema.
2. Rechazar transición no permitida.
3. Bloquear `risk: high` antes de invocar un Coder.
4. Verificar ownership lock antes de escribir.
5. Limitar herramientas y rutas por rol/scope.
6. Registrar el modelo realmente usado, incluidos fallbacks.
7. No conceder commit, push, merge, secretos o instalación de dependencias.
8. Finalizar en `PENDING_ACCEPTANCE`, nunca `DONE`.

## Fallback

Si una capacidad de OpenCode no está disponible, la tarea pasa a `BLOCKED` o
se ejecuta manualmente usando los mismos contratos. No se reduce un gate para
mantener el flujo en movimiento.
