---
document_id: FF-ADR-0005
status: accepted
machine_context: true
---

# ADR 0005: Capacidad atomica en creacion de Booking

- **Estado:** Accepted
- **Fecha:** 2026-08-12

## Contexto

Una comprobacion de `available_spots` realizada fuera de la operacion de creacion puede quedar obsoleta por concurrencia y permitir overbooking.

## Decision

La creacion de Booking debe tener una comprobacion transaccional protegida de capacidad y duplicados. La capa service puede realizar validaciones tempranas para UX/negocio, pero la integridad final depende de la operacion atomica de persistencia.

## Responsabilidades

- Service: estado de sesion, membership, allowed plan y reglas de negocio.
- CRUD/transaccion: capacidad, duplicado y creacion atomica.
- DB: constraints/locks que aporten integridad estructural.
- Router: mapear `ConflictError` u otros errores al contrato HTTP.

## Consecuencias

- evita confiar en valores calculados en memoria;
- requiere tests de concurrencia/integracion suficientes;
- no permite mover por comodidad la regla comercial de memberships al CRUD.
