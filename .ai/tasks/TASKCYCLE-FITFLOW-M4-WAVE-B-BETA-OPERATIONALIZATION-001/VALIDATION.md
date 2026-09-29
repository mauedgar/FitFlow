# Validation

Status: `PASS`

Validated candidate before evidence-only freeze:
`380ba3d988687ab917258644fddef5e594e2e407`.

| Gate | Command scope | Result | Evidence |
| --- | --- | --- | --- |
| baseline | `git` branch, commit, tree, and porcelain status in canonical checkout | PASS | `develop`, `eb7ed59c...`, `2b49b09...`, clean |
| Compose render | staging Compose with explicit non-secret local validation inputs | PASS | config rendered without error |
| R005 deploy | `scripts/staging/release.ps1 -Action deploy` | PASS | four healthy services; revision/config digest and `e4f5a6b7c8d9 (head)` recorded |
| R005 redeploy | `scripts/staging/release.ps1 -Action redeploy` | PASS | same revision force-recreated; volumes and migration head preserved |
| R005 rollback | R005 detached worktree, `-Action rollback -DatabaseForwardCompatible` | PASS | `380ba3d... -> d7c4b34...`; exact head equality; `migrations_downgraded: false` |
| restore candidate | terminal worktree, `-Action deploy` | PASS | terminal application restored with retained PostgreSQL state |
| R006 smoke | `scripts/staging/smoke.ps1`, two consecutive fixture resets/runs | PASS | full proxy/auth/class/session/booking/front-desk/logout flow passed twice |
| post-rollback smoke | one fixture reset/run after terminal restoration | PASS | full vertical passed |
| backend regression | migrate fresh `fitflow-wave-b-test`, then `python -m pytest tests` | PASS | `130 passed, 1 warning` |
| frontend regression | revision image build executes `npm ci`, TypeScript, and Vite build | PASS | production frontend image built successfully |
| changed Python lint | Ruff in pinned test image, ignoring Windows bind-mount-only `EXE002` | PASS | all checks passed; Git modes verified `100644` |
| PowerShell syntax | parser checks for release and smoke operators | PASS | no parser errors |
| migration | `alembic current` inside terminal backend | PASS | `e4f5a6b7c8d9 (head)` |
| liveness/readiness | release checks plus R006 smoke | PASS | `alive`; `ready` with PostgreSQL and Redis |
| logging visibility | bounded backend startup/access/error log inspection | PASS | migration/startup and complete HTTP vertical visible |
| R007 evidence binding | YAML parse and authority assertions | PASS | only READY/NOT_READY decision outcomes; launch authority false |

The first fresh regression attempt was `NOT_RUN_VALIDLY`: the newly created test
database had not yet received migrations and produced only missing-relation
errors. After `alembic upgrade head`, the unchanged suite passed `130/130`.

Security observation: refresh and logout currently receive refresh tokens as
query parameters, and access logs record request URLs. Token values are omitted
from this evidence. This activates the R007 incident/stop condition and makes
the current controlled-beta decision `NOT_READY_FOR_BETA_DECISION`. It does not
change the PASS result for implementation of the R005-R007 operational contract.
