# ADR 0007: Dos pipelines complementarios de desarrollo con IA

- **Estado:** Accepted
- **Fecha:** 2026-08-12

## Contexto

FitFlow necesita aprovechar un agente potente para tareas complejas sin renunciar a una rama local economica para trabajo cotidiano. Un unico orquestador local no es requisito del MVP y forzarlo agregaria fragilidad.

## Decision

Mantener dos pipelines independientes que consumen la misma documentacion canonica:

1. **Codex + Project Index** como pipeline principal de mayor capacidad.
2. **AiderDesk local** como rama operativa diaria, con Explorer / Worker / Reviewer evolucionando por pruebas.

El Project Index puede producir un Context Package neutral reutilizable. Aider conserva su RepoMap como capacidad propia de runtime.

## Consecuencias

- cada pipeline puede evolucionar sin bloquear al otro;
- se evita duplicar exploracion cara en el pipeline potente mediante indice reutilizable;
- la rama AiderDesk puede seguir siendo experimental hasta alcanzar fiabilidad;
- requiere una jerarquia de source of truth comun para evitar divergencias.
