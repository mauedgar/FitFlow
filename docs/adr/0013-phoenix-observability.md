---
document_id: FF-ADR-0013
status: superseded
machine_context: true
superseded_by: FF-ADR-0017
---

# ADR 0013: Phoenix como observabilidad inicial

- **Estado:** Superseded por ADR 0017
- **Fecha:** 2026-08-16

## Contexto

La orquestación y recuperación no pueden afinarse con impresiones. Deben
correlacionarse tarea, contexto, modelo, validación, costo y resultado.

## Decisión

Adoptar Phoenix como primera capa de trazas por ser accesible para el piloto.
Emitir OpenTelemetry/OpenInference cuando la integración lo permita.

Toda traza debe correlacionar:

- `task_id`, `run_id`, `stage` y `role`;
- proveedor/modelo y nivel de razonamiento;
- revisión/fingerprint e índice;
- query y IDs de chunks, sin secretos ni contenido sensible innecesario;
- tokens/latencia cuando estén disponibles;
- estado de review, validación y aceptación humana.

## Privacidad

Aplicar allowlist de atributos, redacción de secretos y retención limitada. No
capturar `.env`, credenciales, tokens, prompts con secretos ni código fuera del
scope autorizado.

## Gate

Phoenix no bloquea el primer índice. Se incorpora después del pipeline base y
antes de ampliar routing/autonomía. Promptfoo evalúa prompts/modelos una vez
que existen fixtures y resultados deterministas.
