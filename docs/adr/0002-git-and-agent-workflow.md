---
document_id: FF-ADR-0002
status: amended
machine_context: true
amended_by: [FF-ADR-0014, FF-ADR-0016]
---

# ADR 0002: Git y trabajo aislado de agentes

- **Estado:** Amended
- **Fecha:** 2026-08-12
- **Enmienda:** 2026-08-18

## Contexto

FitFlow utiliza agentes capaces de modificar varios archivos y, en algunos entornos, worktrees/ramas de tarea. Se necesita trazabilidad y una forma de evitar que una tarea experimental contamine el estado estable.

## Decision

Git es el sistema de versionado y trazabilidad del proyecto. Los agentes deben trabajar en cambios acotados y, cuando el entorno lo soporte o exista paralelismo, en ramas/worktrees de tarea aislados.

Reglas:
- cambios de agentes deben ser revisables como diff;
- no mezclar cambios no relacionados en una misma tarea;
- arquitectura/dominio no se integran automaticamente sin aprobacion;
- los tests y validaciones forman parte del handoff;
- los agentes no crean commits, push, merge ni integraciones sin autorización
  explicita del desarrollador;
- el historial Git es evidencia, pero no reemplaza ADRs/documentacion del por que.

## Consecuencias

- facilita revertir y revisar;
- permite ejecuciones del desarrollador o asistidas en ramas operativas distintas;
- requiere disciplina para no acumular worktrees/branches abandonados.

La política activa de ownership y paralelismo se define en
`docs/process/risk-and-parallelism.md`.
