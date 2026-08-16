---
document_id: FF-AI-ROLES-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Roles y routing de modelos

## Roles activos

| Rol | Entrada | Salida | Escritura de producto |
| --- | --- | --- | --- |
| Orchestrator | solicitud + estado | dispatch/transición | no |
| Planner/Audit | TASK + doctrina | PLAN, riesgo, ownership | no |
| Explorer | pregunta + scope | Context Package | no |
| Coder A | plan + contexto | implementación media | sí, acotada |
| Coder B | instrucción literal | cambio básico | sí, acotada |
| Reviewer | diff + contrato | REVIEW | no |
| Validator | comandos + diff | VALIDATION | no, salvo artefactos de evidencia |

No habilitar otros roles hasta nueva decisión.

## Niveles de razonamiento

- `low`: extracción literal o edición mecánica cerrada.
- `medium`: implementación acotada con varias dependencias conocidas.
- `high`: planificación, arquitectura, review crítico o ambigüedad relevante.

Riesgo y razonamiento son dimensiones distintas: una tarea simple sobre una
migración destructiva sigue siendo riesgo alto y queda bloqueada.

## Matriz inicial

| Rol | Capacidad requerida | Candidatos iniciales | Prohibición |
| --- | --- | --- | --- |
| Planner/Audit | razonamiento fuerte, visión transversal | GPT de mayor capacidad o Grok equivalente | modelos locales pequeños no deciden arquitectura |
| Explorer | búsqueda, síntesis con citas | modelo general; FastContext como buscador; Qwen Coder 7B tras evaluación | no inventar símbolos/rangos |
| Coder A | edición multiartefacto media | GPT/Copilot/Grok de coding; Qwen 2.5 Coder 7B tras benchmark | no riesgo alto |
| Coder B | edición literal y localizada | Qwen 2.5 Coder 3B o modelo liviano | no decisiones, DB, auth o contratos cruzados |
| Reviewer | independencia y razonamiento fuerte | GPT/Grok distinto de la ejecución coder; DeepSeek R1 8B como segunda opinión acotada | no aprobar su propia implementación |
| Validator | ejecución determinista | herramientas primero; LLM liviano para diagnóstico | no declarar PASS sin ejecutar |

“Copilot” se trata como superficie/provider de modelos disponibles, no como un
modelo único. Registrar el ID efectivo.

## Selección

1. Filtrar por rol, riesgo, contexto y herramientas.
2. Elegir el candidato más económico que haya superado el benchmark del tipo de
   tarea.
3. Usar fallback solo si conserva capacidad y políticas.
4. Registrar selección y fallback.
5. Promover o degradar candidatos por métricas, no por una impresión aislada.

## Criterios de promoción local

Un modelo local se habilita por rol cuando cumple un set estable de fixtures,
no excede el presupuesto de retrabajo y no aumenta fallos críticos. La
promoción es específica por `role + task_type + risk`, nunca global.
