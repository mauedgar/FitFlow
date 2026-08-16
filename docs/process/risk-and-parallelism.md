---
document_id: FF-PROCESS-RISK-001
status: canonical
machine_context: true
version: 1.0
updated: 2026-08-16
---

# Riesgo y paralelismo

## Clasificación conservadora

| Riesgo | Ejemplos | Ejecución IA |
| --- | --- | --- |
| low | docs, tests aislados, edición mecánica sin contrato cruzado | permitida |
| medium | feature/refactor acotado con dependencias conocidas | permitida con reviewer + validator |
| high | auth, permisos, secretos, transacción crítica, migración destructiva, dependencia base, arquitectura/dominio transversal | bloqueada |

Ante duda, usar la categoría superior. Solo una persona puede recortar alcance y
reclasificar.

## Ownership keys

Toda task declara una o más claves:

- `path:<ruta-o-glob-resuelto>`;
- `api:<método>:<ruta>`;
- `domain:<concepto>`;
- `db:<tabla-o-migración>`;
- `doc:<document_id>`;
- `config:<sistema>`.

Los globs deben resolverse a rutas explícitas antes de tomar lock.

## Regla de paralelismo

Dos tareas pueden ejecutar en paralelo si la intersección de claves es vacía y
ninguna consume el contrato todavía no aceptado de la otra. Reader/reader es
compatible; writer/reader o writer/writer sobre la misma clave se serializa.

## Bloqueos

El lock registra task, run, owner, modo, timestamp y expiración. Un lock vencido
no se roba automáticamente: se verifica que la ejecución anterior terminó.

## Ejemplos

- Test unitario de frontend y auditoría read-only de docs disjuntas: paralelo.
- Service Booking y router Booking: serializar por contrato compartido.
- Dos docs distintos que modifican la misma decisión: serializar por
  `doc/architecture` o `domain`.
- Backend y frontend de un contrato nuevo: serializar plan/contrato; luego
  paralelizar implementaciones si el contrato quedó congelado.
