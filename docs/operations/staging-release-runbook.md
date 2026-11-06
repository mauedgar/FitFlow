---
document_id: FF-OPS-STAGING-RELEASE-001
status: accepted_pending_implementation
machine_context: true
milestone: M4_STAGING_AND_BETA_READINESS
responsibility: R005
---

# Staging deployment, redeploy, and rollback

## Scope

This provider-neutral procedure operates only the repository's staging-like
Docker Compose topology. It does not select a host, provision infrastructure,
configure DNS or TLS, publish images, or deploy externally.

The release identity is the full Git commit. Backend and frontend images are
tagged and labelled with `FITFLOW_REVISION`. The operator script refuses a
requested revision that is not the checked-out `HEAD`, a checkout with tracked
or untracked changes, or a checkout containing Git-ignored untracked files
inside the Docker-copied `backend/` or `frontend/` source trees. Use one clean,
isolated Git worktree per revision.

## Configuration material

Supply secrets through the process environment or an untracked environment
file. Never commit the populated file. Required values are:

- `POSTGRES_PASSWORD`;
- `SECRET_KEY`;
- `BACKEND_CORS_ORIGINS`.

The remaining non-secret inputs and defaults are documented in
`.env.staging.example`. The operator resolves the effective values first, exports
those same values into the Compose process environment, and then records a
SHA-256 digest of them: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`SECRET_KEY`, `BACKEND_CORS_ORIGINS`, `LOG_LEVEL`, `STAGING_BACKEND_PORT`,
`STAGING_FRONTEND_PORT`, and `VITE_API_BASE_URL`, plus `FITFLOW_TIMEZONE` (default `America/Argentina/Buenos_Aires`). The backend receives `FITFLOW_TIMEZONE`; the frontend Docker build arg `VITE_FITFLOW_TIMEZONE` is sourced from that same value. The release script rejects a conflicting `VITE_FITFLOW_TIMEZONE` process override and invalid timezone identifiers. The frontend reads this value only at build time, so a timezone change requires a new image build. The operator also forces
`COMPOSE_DISABLE_ENV_FILE=1` before invoking Compose, so Compose does not load the
default project `.env`; the values represented by `configuration_sha256` are the
explicit process-environment inputs consumed for interpolation. `-EnvFile` is
imported before this normalization step and is still passed explicitly to Compose,
so its selected values are also exported and hashed. Secret contents are never
written to deployment state. Preserve the exact approved configuration material
outside Git if a later application rollback must reproduce it.

## Prerequisites

- a clean isolated worktree at the exact release commit, with no Git-ignored
  untracked files inside the Docker-copied `backend/` or `frontend/` trees;
- Git, PowerShell 7+, Docker Engine, and Docker Compose;
- populated staging configuration in process environment or an untracked file;
- explicit isolated Compose project name via `-ProjectName`; historical
  `fitflow-staging` and `fitflow` projects are rejected;
- explicit, distinct ports `STAGING_BACKEND_PORT` and
  `STAGING_FRONTEND_PORT`, excluding reserved historical ports 18000/18080;
- no existing state, project containers or volumes for initial deployment.
  Ports are published on 127.0.0.1 only and images are project-namespaced.

Example invocation from the release worktree:

```powershell
$env:STAGING_BACKEND_PORT = "18100"
$env:STAGING_FRONTEND_PORT = "18180"
pwsh ./scripts/staging/release.ps1 -Action preflight -ProjectName fitflow-m4-qual-001 -Revision (git rev-parse HEAD)
# Deploy requires separately verified environment and effect authorization:
pwsh ./scripts/staging/release.ps1 -Action deploy -ProjectName fitflow-m4-qual-001 -Revision (git rev-parse HEAD)
```

Use `-EnvFile <untracked-path>` when configuration is stored in a local file.
Use `-StateDirectory <external-path>` to choose the location of
`deployment-state.json`. The default is the current user's local application
data directory.

## Deploy

1. Resolve and verify the full commit and clean worktree.
2. Validate required configuration without printing secret values.
3. Render and validate `docker-compose.staging.yml`.
4. Build revision-tagged backend and frontend images.
5. Start PostgreSQL and Redis, then start the migration-first backend, then the
   Nginx frontend.
6. Wait for Compose health checks.
7. Verify backend liveness, dependency readiness, and the frontend root.
8. Record revision, previous revision, configuration digest, and Alembic
   revision in `deployment-state.json`.

The backend startup command runs `alembic upgrade head` before Uvicorn. A failed
migration prevents the backend and dependent frontend from becoming healthy.

## Redeploy

Redeploy is an in-place replacement of the same recorded revision:

```powershell
pwsh ./scripts/staging/release.ps1 -Action redeploy -ProjectName fitflow-m4-qual-001 -Revision (git rev-parse HEAD)
```

The command rebuilds the images and force-recreates services while preserving
the named PostgreSQL and Redis volumes. Migration startup remains idempotent at
the same Alembic head. The same liveness, readiness, frontend, and database
revision checks run after replacement. The script refuses redeploy if runtime
state does not identify the same revision.

## Application rollback

Rollback is an application and configuration operation, not a database
downgrade. Prepare a clean isolated worktree at the exact target commit and use
the target's reviewed configuration material:

```powershell
pwsh ./scripts/staging/release.ps1 `
  -Action rollback `
  -ProjectName fitflow-m4-qual-001 `
  -Revision (git rev-parse HEAD) `
  -DatabaseForwardCompatible
```

The automated rollback path is intentionally conservative:

- a different currently deployed revision must exist in runtime state;
- the operator must explicitly confirm application/database compatibility;
- the live database revision must exactly equal the target source's Alembic
  head;
- named PostgreSQL and Redis volumes are preserved;
- `alembic downgrade` is never invoked;
- all post-release health and revision checks must pass.

If the live database revision differs from the target head, rollback is unsafe
for this procedure and stops before application replacement. Return to CONTROL
for a reviewed forward-fix, data restoration plan, or a separately authorized
database recovery. Do not infer compatibility from a successful image build.

## Safe and unsafe conditions

Safe automated conditions:

- clean target source, including no ignored untracked files in Docker-copied
  source trees, and immutable full commit identity;
- known configuration material and configuration digest;
- healthy PostgreSQL and Redis;
- exact live/target Alembic revision equality;
- no migration downgrade or volume deletion;
- post-operation liveness, readiness, frontend, and migration checks pass.

Unsafe conditions requiring STOP:

- missing or ambiguous release/configuration identity;
- dirty source or uncommitted runtime changes;
- live database revision differs from the rollback target head;
- target application requires destructive data conversion;
- recovery requires `down --volumes`, `alembic downgrade`, or manual DB edits;
- external provider, DNS, TLS, or security policy decisions are required.

## Runtime state and reset boundary

PostgreSQL is persistent product state. Redis is temporary authentication state,
but neither volume is deleted by deploy, redeploy, or rollback. Destructive
volume reset is outside R005 and must never be used on retained staging data.
The R006 smoke environment defines its own isolated, explicitly destructive
reset boundary.

## Isolated staging preflight

`-Action preflight` only verifies exact clean worktree identity, required
configuration, Compose rendering and empty project state/containers/volumes.
It does not build, start services, migrate, seed, write release state or qualify
runtime. Its result `CONFIG_PREFLIGHT_ONLY` is neither R002–R006 PASS nor
permission to deploy. Port liveness, secrets provenance, backup, TLS and data
safety still require separate native checks and a competent effect grant.

State defaults to a project-specific local app-data directory:
`FitFlow/staging/<ProjectName>/deployment-state.json`. The example ports above
are illustrative and must be checked against real host listeners first.

Direct `docker compose up` without an explicit project identity is not a
supported release path: Compose requires `FITFLOW_COMPOSE_PROJECT` and
`FITFLOW_RELEASE_IMAGE_NAMESPACE` instead of defaulting to historical names.
Use `release.ps1`, which supplies both values and checks project ownership.

The first-deployment refusal includes preexisting project-namespaced Docker
networks, not only containers and volumes. This protects against unintentionally
joining an unrelated or stale Compose network. The preflight does not remove or
recreate any network; an existing collision is `BLOCKED_PRECONDITION`.

## Retained-resource ownership receipt (schema v2)

`redeploy` and `rollback` reject historical or incomplete state. Before any
build or migration, the operator requires an exact matching configuration digest,
full previous revision/tree metadata and recorded backend/frontend image IDs.
It then verifies four running project-labelled services, the exact backend and
frontend revision labels and published loopback ports, PostgreSQL/Redis named
mounts and Compose-owned volume/network labels. Inventory and image IDs are
checked again immediately before `up`; new post-release identities and source
tree SHA are stored in the v2 receipt with `cleanup_performed=false`.
Schema v1 receipts are intentionally not upgraded automatically.
A configuration change on retained state is blocked pending separate review.

These checks do not make Docker inventories atomic: a qualified exclusive host
and project owner are required before authorizing any real execution.
