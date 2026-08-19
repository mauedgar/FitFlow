---
artifact: PLAN
schema_version: fitflow-plan/v2
task_id: FF-AI-VNEXT-001
run_id: FF-AI-VNEXT-001-20260818
status: PASS
created_at: "2026-08-18T00:00:00-03:00"
author_role: developer_planner
risk: medium
ownership_keys:
  - "doc:baseline-vnext"
  - "config:ai-v2"
  - "path:../FitFlow-ai/docs"
---

# Resultado esperado

Baseline vNext 5.0 coherente, verificable y lista para aceptacion del
desarrollador, con implementacion posterior dividida en tasks pequenas.

## Pasos

| ID | Responsable | Accion | Output | Gate |
| --- | --- | --- | --- | --- |
| P1 | developer planner | contrastar v4 e informes | matriz de decisiones | evidencia trazable |
| P2 | developer planner | actualizar doctrina y ADR | baseline machine | sin contradicciones activas |
| P3 | developer planner | definir config/contracts v2 | YAML/JSON Schema | parse y ejemplos PASS |
| P4 | developer planner | redefinir backlog/FitFlow-ai | roadmap | no claim falso |
| P5 | developer planner | generar DOCX | 3 documentos + 6 fuentes | estructura/a11y PASS |
| P6 | validator | ejecutar gates | VALIDATION | estados normalizados |
| P7 | reviewer independiente | inspeccionar diff | REVIEW | PASS o correccion |
| P8 | workflow | crear bundle y result | ZIP + RESULT | PENDING_ACCEPTANCE |

## Rutas de fallo

| Condicion | Transicion |
| --- | --- |
| contradiccion de doctrina | PLANNING |
| schema/config invalido | ROUTING |
| herramienta ausente | BLOCKED o UNAVAILABLE segun gate |
| review con findings | ROUTING |
| decision no cerrada | WAITING_DEVELOPER |
