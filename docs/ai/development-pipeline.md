---
document_id: FF-AI-PIPELINE-DEV-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Pipeline de desarrollo asistido

## Entrada

Una solicitud puede ser `use_case`, `feature`, `fix`, `refactor`, `audit`,
`test`, `docs` o `tooling`. Debe convertirse en `TASK.md` antes de ejecutar.

## Estados y gates

| Estado | Responsable | Salida obligatoria | Gate |
| --- | --- | --- | --- |
| INTAKE | Orchestrator | TASK draft | objetivo identificable |
| PLAN | Planner/Audit + persona si aplica | PLAN | scope, riesgo, ownership, AC |
| EXPLORE | Explorer | CONTEXT_REQUEST/PACKAGE | evidencia suficiente y fresca |
| EXECUTE | Coder A/B | IMPLEMENTATION | scope respetado + self-check |
| REVIEW | Reviewer | REVIEW | `PASS` o ruta de corrección |
| VALIDATE | Validator | VALIDATION | gates ejecutados y trazables |
| PENDING_ACCEPTANCE | Orchestrator | RESULT | persona revisa |
| DONE | persona | integración aceptada | revisión/commit externo al agente |

## Routing de ejecución

- Coder B: cambio literal, una responsabilidad, riesgo bajo, sin contrato
  cruzado.
- Coder A: tarea media con varias piezas dentro de un ownership delimitado.
- Riesgo alto: `BLOCKED_HIGH_RISK`; no se asigna coder.

## Rutas de fallo

| Detección | Estado siguiente | Límite |
| --- | --- | --- |
| falta evidencia | EXPLORE | 2 rondas |
| defecto localizado | EXECUTE | 2 correcciones |
| tests fallan por implementación | EXECUTE | 2 correcciones |
| plan/scope/doctrina incorrectos | PLAN | decisión requerida |
| conflicto de ownership | BLOCKED | hasta liberar lock |
| dependencia/entorno ausente | BLOCKED | registrar `UNAVAILABLE` |
| riesgo alto descubierto | BLOCKED_HIGH_RISK | solo persona reclasifica |
| validación final falla | EXECUTE o PLAN | según causa |

Agotado un límite, no improvisar: producir RESULT parcial y escalar.

## Validación humana crítica

Obligatoria para arquitectura/dominio, auth/permisos, transacciones críticas,
migraciones destructivas, dependencias base, secretos, cambios de contratos
transversales, promoción de docs y aceptación final.

## Cierre

`RESULT.md` consolida archivos, evidencia, riesgos, impacto documental y pasos
siguientes. No incluye transcript ni razonamiento privado.
