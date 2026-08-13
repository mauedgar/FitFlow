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

Desde `backend/`:

```text
python -m pytest
python -m pytest -m smoke
python -m pytest -m unit
python -m pytest -m "integration or api"
```

Desde root usar los wrappers en `scripts/quality/`.

## Estado

El smoke de harness incluido prueba que pytest recolecta/ejecuta. NO demuestra que FitFlow este cubierto. La task FF-LOCAL-001 debe conectar fixtures reales y agregar tests significativos.
