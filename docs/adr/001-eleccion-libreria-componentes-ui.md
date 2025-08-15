# ADR 001: Elección de la Librería de Componentes de UI

- **Estado:** Aceptado
- **Fecha:** 2025-08-16

## Contexto

El proyecto necesita una forma eficiente y escalable de construir la interfaz de usuario. Se requiere un sistema que permita un desarrollo rápido, mantenga la consistencia visual y sea fácil de aprender para futuros desarrolladores.

## Decisión

Se ha decidido utilizar **Chakra UI** como la librería de componentes principal para el frontend de FitFlow.

## Consecuencias

- **Positivas:**

  - **Desarrollo rápido:** Provee una gran cantidad de componentes pre-construidos (botones, modales, layouts) listos para usar.
  - **Accesibilidad:** Chakra UI pone un fuerte énfasis en la accesibilidad (WAI-ARIA standards).
  - **Personalizable:** Permite extender y modificar el tema por defecto para que coincida con la marca de FitFlow.
  - **Excelente experiencia de desarrollador:** La sintaxis basada en props es muy intuitiva.

- **Negativas:**
  - Añade una dependencia significativa al proyecto.
  - El tamaño final del bundle puede ser mayor que con soluciones "utility-first" como Tailwind.

## Alternativas Consideradas

- **Tailwind CSS:** Fue la primera opción considerada. Sin embargo, durante la fase de configuración inicial, se encontraron problemas persistentes de compatibilidad y ejecución de scripts (`npx`) que bloquearon el desarrollo. Para no retrasar el sprint, se decidió optar por una alternativa más estable en nuestro entorno.
- **CSS Modules / Styled Components:** Ofrecen un control más granular pero requieren escribir mucho más CSS desde cero, ralentizando la fase inicial del proyecto.
- **Mantine UI:** Una alternativa muy similar a Chakra UI, considerada como Plan B si Chakra también presentaba problemas.
