# Contratos serializados

## Autoridad y alcance

Este directorio contiene el contrato consumidor para artefactos operativos del
AI Core. No contiene los schemas Pydantic/OpenAPI del producto y no ejecuta la
maquina de estados.

Los contratos Zod ejecutables y el runtime generico pertenecen a FitFlow-ai.
FitFlow conserva esta representacion JSON Schema para validar sus TASK, runs y
evidencia contra el baseline declarado. Los archivos v2 no se modifican
unilateralmente ni se usan para redefinir la politica interna del AI Core.

La distribucion desde FitFlow-ai permanece `MIGRATION_PENDING`; no se ha
adoptado como canonico npm, submodulo ni otro mecanismo. Toda actualizacion
requiere version productor, analisis de compatibilidad, validacion del consumidor
y cambio explicito de baseline. Una divergencia se registra y bloquea el cambio
afectado; no se corrige mediante aliases silenciosos.

## Activos

Los runs vNext usan Draft 2020-12 bajo `v2/`. Los schemas v1 en la raiz se
conservan para lectura de historial y no se modifican.

| Artefacto | Schema v2 |
| --- | --- |
| TASK | `v2/task.schema.json` |
| RouteDecision | `v2/route-decision.schema.json` |
| ContextRequest | `v2/context-request.schema.json` |
| ContextPackageResult | `v2/context-package-result.schema.json` |
| ExecutionResult | `v2/execution-result.schema.json` |
| ValidationResult | `v2/validation-result.schema.json` |
| ReviewResult | `v2/review-result.schema.json` |
| DocImpact | `v2/doc-impact.schema.json` |
| RunEvent / RunState | `v2/run-event.schema.json` / `v2/run-state.schema.json` |
| UsageRecord / FinOpsSummary | `v2/usage-record.schema.json` / `v2/finops-summary.schema.json` |
| RunResult | `v2/run-result.schema.json` |

## Migracion v1 -> v2

- `author_role: human` -> `author_role: developer`;
- lane `human` -> `developer`;
- `PLAN` -> `PLANNING`, `EXPLORE` -> `EXPLORING`, `EXECUTE` -> `EXECUTING`,
  `VALIDATE` -> `VALIDATING`, `REVIEW` -> `REVIEWING`;
- el orden historico review/validate se conserva en runs v1 y no se reescribe;
- `baseline_revision` + `working_tree_fingerprint` -> objeto `baseline`;
- modelos y providers se resuelven en UsageRecord, no dentro del rol;
- artefactos v1 y v2 no comparten `run_id`.

Un migrador debe producir un reporte de campos transformados y rechazados. No
acepta aliases silenciosos ni infiere runtime IDs.
