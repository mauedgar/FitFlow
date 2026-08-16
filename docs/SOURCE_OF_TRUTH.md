---
document_id: FF-SOT-001
status: canonical
machine_context: true
version: 4.0
updated: 2026-08-16
---

# Source of Truth de FitFlow

## Propósito

Resolver contradicciones y evitar que un resumen generado adquiera autoridad
sobre el sistema real.

## Capas de autoridad

| Orden | Capa | Autoridad |
| --- | --- | --- |
| 0 | realidad ejecutable | código, tests, configuración, modelos, migraciones y estado reproducible |
| 1 | doctrina canónica | arquitectura, dominio, estado, calidad, roadmap, proceso y ADR aceptados |
| 2 | registros operativos | TASK, PLAN, STATUS, IMPLEMENTATION, REVIEW, VALIDATION y RESULT |
| 3 | contexto derivado | inventarios, XML estructural, Repomix, embeddings, Qdrant y caches |
| 4 | material humano/histórico | `docs/archive/` |

Los tests solo prueban el comportamiento cubierto. Una decisión aceptada pero
no implementada pertenece a doctrina, no a realidad ejecutable.

## Fuentes derivadas autorizadas

Para seleccionar contexto se autorizan:

1. inventario de directorios del scope;
2. XML fechado de clases y relaciones;
3. bundle Repomix acotado;
4. recuperación vectorial mediante LlamaIndex/Qdrant;
5. búsqueda y lectura directa en el repositorio.

Todo artefacto derivado debe incluir revisión base o fingerprint, fecha,
generador, exclusiones y hash. Si no coincide con el working tree, es `STALE`.

## Conflicto

1. Identificar fuentes y revisiones.
2. Verificar el código y el alcance real de los tests.
3. Clasificar la contradicción: estado, intención, doctrina o artefacto obsoleto.
4. Registrar `DECISION_REQUEST.md` si cambia una decisión durable.
5. Bloquear la edición cuando resolverla ampliaría scope o riesgo.
6. Promover el resultado aceptado a docs/ADR mediante una tarea separada o un
   criterio explícito de la tarea actual.

## Estados documentales

- `canonical`: gobierna el presente.
- `accepted_pending_implementation`: decisión aprobada no confirmada en código.
- `planned`: dirección futura.
- `review_required`: evidencia incompleta o contradictoria.
- `historical`: trazabilidad sin autoridad.
- `superseded`: reemplazado por un documento identificado.

## Promoción

Solo promover a doctrina cambios durables de comportamiento, invariantes,
fronteras, calidad, proceso o roadmap. Logs, razonamiento interno, resultados de
búsqueda y texto explicativo no se promueven.
