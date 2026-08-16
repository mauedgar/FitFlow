---
document_id: FF-AI-PIPELINE-VALIDATION-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Pipeline de validación

## Entrada

TASK, PLAN, diff revisado, baseline/fingerprint y lista de gates aprobada.

## Etapas

1. **Preflight:** verificar revisión, entorno y permisos; no instalar.
2. **Schema/format:** validar artefactos y contratos afectados.
3. **Targeted:** ejecutar tests/checks directamente vinculados.
4. **Affected suite:** obligatoria para riesgo medium.
5. **Static:** Ruff/Pyright y herramientas canónicas aplicables.
6. **Boundary:** Alembic/OpenAPI/API/frontend según impacto.
7. **Classify:** asignar estado y clase de fallo por gate.
8. **Route:** recomendar el estado siguiente.

## Routing

| Resultado | Siguiente estado |
| --- | --- |
| todos PASS/N/A justificados | PENDING_ACCEPTANCE |
| defecto de implementación | EXECUTE |
| evidencia faltante | EXPLORE |
| plan/baseline incorrecto | PLAN |
| entorno/herramienta ausente | BLOCKED |
| riesgo alto descubierto | BLOCKED_HIGH_RISK |

## Reglas

- El Validator no corrige código.
- Un diagnóstico LLM no sustituye exit code/output.
- `N/A` requiere justificación; `NOT_RUN` y `UNAVAILABLE` no son éxito.
- Logs extensos quedan fuera del documento; conservar comando, exit code,
  alcance y resumen reproducible.
