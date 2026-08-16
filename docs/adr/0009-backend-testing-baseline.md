---
document_id: FF-ADR-0009
status: accepted
machine_context: true
---

# ADR 0009: Pytest como baseline de validacion backend

- **Estado:** Accepted / Pending Full Coverage
- **Fecha:** 2026-08-13

## Contexto

La operacion con agentes necesita validaciones deterministas. Sin una suite ejecutable, el agente debe inferir regresiones leyendo mas contexto y la Definition of Done no puede comprobarse de forma consistente.

## Decision

Adoptar **pytest + pytest-asyncio** como baseline de testing backend y una estructura estable por tipo de prueba:

- smoke;
- unit;
- integration;
- api;
- concurrency.

Se incluyen templates no recolectables por pytest y wrappers de ejecucion para agentes.

## Principios

- tests deterministas y aislados;
- unit tests para reglas aislables;
- integration tests para DB/CRUD/transacciones;
- API tests para contratos HTTP;
- concurrency tests para invariantes como overbooking cuando corresponda;
- los tests forman parte de Validation, no sustituyen review;
- la existencia del harness no equivale a cobertura completa.

## Consecuencias

### Positivas
- feedback reproducible;
- menor necesidad de inferencia del agente;
- habilita gates futuros de CI/orquestacion;
- protege refactors/naming/movimientos de archivos.

### Negativas
- requiere fixtures y mantenimiento;
- integration/concurrency tests pueden ser mas lentos;
- la primera adopcion necesita reconciliar dependencias y DB de test reales.
