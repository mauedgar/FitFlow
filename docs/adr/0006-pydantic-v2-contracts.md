# ADR 0006: Pydantic v2 como capa de contratos

- **Estado:** Accepted
- **Fecha:** 2026-08-12

## Contexto

Durante la refactorizacion aparecio confusion entre modelos ORM, payloads de entrada, respuestas publicas y estructuras internas.

## Decision

Usar Pydantic v2 como capa explicita de contratos y validacion estructural. Mantener nombres que expresen proposito (`Create`, `Update`, `Public`, `Internal`, vistas especificas) y evitar reutilizar schemas ambiguos.

Pydantic no es propietario de reglas que dependan del estado de DB.

## Consecuencias

- contratos mas claros para FastAPI y frontend;
- reduce ciclos/mezcla con ORM;
- exige revisar schemas junto con endpoints y services durante Sprint 6.8.
