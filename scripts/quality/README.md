# Quality wrappers

Wrappers pensados para humanos/agentes en Windows.

- `run_backend_tests.ps1`: construye/inicia exclusivamente el proyecto Compose
  `fitflow-test` y ejecuta pytest dentro de `backend_test`.
- `run_backend_validation.ps1`: ejecuta pytest y, si están disponibles en la
  imagen, Ruff y Pyright dentro de `backend_test`.

Los wrappers no ejecutan pytest con el Python local y no utilizan la base de
desarrollo. `UNAVAILABLE` es un estado explícito para herramientas no instaladas.

Los wrappers dejan el entorno de pruebas activo para inspección. Para retirar
solo sus contenedores y red, conservando el volumen:

```powershell
docker compose --project-name fitflow-test --file docker-compose.test.yml rm --stop --force backend_test postgres_test
docker network rm fitflow-test_test_network
```
