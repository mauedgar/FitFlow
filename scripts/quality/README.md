# Quality wrappers

Wrappers pensados para humanos/agentes en Windows.

- `run_backend_tests.ps1`: ejecuta pytest usando `backend/.venv_backend` si existe.
- `run_backend_validation.ps1`: pytest + Ruff + Pyright.

La primera task debe verificar que estos comandos coincidan con el entorno real. `UNAVAILABLE` es un gap, no un PASS.
