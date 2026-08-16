---
document_id: FF-ADR-0001
status: accepted
machine_context: true
---

# ADR 0001: Eleccion de Chakra UI

- **Estado:** Accepted
- **Fecha original:** 2025-08-16

## Contexto

FitFlow necesitaba una forma eficiente y escalable de construir la interfaz, con desarrollo rapido, consistencia visual y una curva de adopcion razonable.

## Decision

Usar **Chakra UI** como libreria principal de componentes del frontend.

## Consecuencias

### Positivas
- gran cantidad de componentes listos para usar;
- foco en accesibilidad;
- tema personalizable;
- buena experiencia de desarrollo basada en props.

### Negativas
- dependencia significativa;
- bundle potencialmente mayor que enfoques utility-first.

## Alternativas consideradas

### Tailwind CSS
Fue la primera opcion considerada, pero durante la configuracion inicial existieron problemas persistentes de compatibilidad/ejecucion de scripts (`npx`) que bloquearon el avance. Se priorizo no retrasar el desarrollo.

### CSS Modules / Styled Components
Mayor control, pero mas CSS manual para la etapa inicial.

### Mantine UI
Alternativa similar, conservada como plan B en aquel momento.

## Estado actual

Chakra UI continua en el stack frontend canonico. Cambiar de libreria requeriria un nuevo ADR y una justificacion que compense el costo de migracion.
