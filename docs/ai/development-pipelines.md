# Pipelines de desarrollo asistido por IA

## 1. Objetivo

Economizar tiempo/contexto sin delegar decisiones ambiguas a una cadena opaca de agentes.

Todas las lanes consumen el mismo contrato de task y entregan el mismo contrato de resultado definido en `docs/process/task-lifecycle-and-reporting.md`.

## 2. Pipeline A - Codex + Project Index

```text
Jira / TASK
  -> Codex
  -> Project Index cuando aporta contexto
  -> lectura del codigo real
  -> plan / implementacion
  -> pytest / lint / type / review
  -> RESULT
```

Codex es el pipeline principal para auditorias/cambios de mayor alcance.

## 3. Pipeline B - AiderDesk local

```text
Jira / TASK
  -> M-Explorer (read-only)
  -> Evidence Handoff
  -> Worker
  -> tests/validation
  -> Reviewer
  -> RESULT
```

La rama AiderDesk sigue en afinacion manual y no bloquea el MVP.

## 4. Contrato de handoff

```text
Task scope
Evidence:
- path
- symbol
- line range
- why relevant
- confidence/source
Direct dependencies
Open questions
```

No pasar el historial completo si la evidencia compacta alcanza.

## 5. Autonomia

Permitido dentro de tasks delimitadas:
- exploracion;
- implementacion local;
- tests/linters;
- fixes directamente derivados de failures reproducibles;
- propuestas fuera de scope sin aplicarlas.

Requiere decision humana:
- dominio/arquitectura;
- dependencias base;
- migraciones destructivas;
- seguridad transversal;
- ampliar MVP;
- superseder ADRs;
- integrar cambios riesgosos no validados.

## 6. Coordinacion

Codex, Aider y humano pueden trabajar sobre tasks diferentes, pero no deben escribir simultaneamente sobre la misma seccion conceptual.

Jira coordina estado; Git aisla implementacion; RESULT normaliza la salida.
