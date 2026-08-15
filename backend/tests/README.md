# Backend tests

Baseline de testing FitFlow.

## Estructura

- `smoke/`: harness y wiring critico.
- `unit/`: reglas aislables.
- `integration/`: DB/CRUD/transacciones.
- `api/`: contratos HTTP.
- `concurrency/`: races/locks/overbooking.
- `helpers/`, `factories/`: utilidades compartidas con ownership claro.
- `_templates/`: ejemplos; pytest no los recolecta.

## Naming

Archivo:
`test_<area>.py`

Funcion:
`test_<behavior>_when_<condition>`

Ejemplo:
`test_rejects_booking_when_session_is_full`

## Politica

- tests deterministas;
- un comportamiento principal por test;
- sin dependencia de orden;
- DB de test aislada;
- no red externa salvo integracion explicita;
- no mockear la regla que se intenta validar;
- mantener fixtures pequenas y legibles.

## Ejecucion

Dentro del contenedor `backend_test`:

```text
python -m pytest
python -m pytest -m smoke
python -m pytest -m unit
python -m pytest -m "integration or api"
```

Desde root usar los wrappers en `scripts/quality/`.

Los tests marcados como `integration`, `api` o `concurrency` deben ejecutarse
con `DATABASE_URL` apuntando a `fitflow_test`. La suite de integración falla
antes de abrir una conexión cuando el nombre de base configurado es otro.

## Estado

El smoke verifica Python y la carga del registro ORM. La cobertura inicial de
Booking comprueba cancelación/re-reserva, preservación de historia ante soft
delete de ClassSession y protección concurrente del último cupo. Esto no implica
cobertura completa del backend ni startup HTTP completo.
