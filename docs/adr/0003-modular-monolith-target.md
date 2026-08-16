---
document_id: FF-ADR-0003
status: accepted
machine_context: true
---

# ADR 0003: Monolito modular como arquitectura objetivo

- **Estado:** Accepted / Pending Implementation
- **Fecha:** 2026-08-12

## Contexto

FitFlow no necesita la complejidad operacional de microservicios para entregar el MVP. Al mismo tiempo, el crecimiento del dominio exige fronteras internas claras y una estructura mantenible.

## Decision

Consolidar gradualmente FitFlow como **Modular Monolith**.

El sistema permanece simple de ejecutar/desplegar, con limites internos por responsabilidades y dominio. No se introducen microservicios, brokers, CQRS o event sourcing para resolver necesidades actuales del MVP.

## Implementacion

La reorganizacion sera incremental despues de estabilizar comportamiento y contratos. No autoriza un big-bang refactor durante Sprint 6.8.

## Consecuencias

### Positivas
- menor complejidad operacional;
- debugging y desarrollo local mas simples;
- limites internos que permiten evolucion futura;
- menor overhead de red/observabilidad distribuida.

### Negativas
- requiere disciplina para preservar fronteras;
- una extraccion futura a servicios exigira trabajo adicional si aparece una necesidad real.
