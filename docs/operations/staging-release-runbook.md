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
requested revision that is not the checked-out `HEAD`, or a checkout with
tracked modifications. Use one clean, isolated Git worktree per revision.

## Configuration material

Supply secrets through the process environment or an untracked environment
file. Never commit the populated file. Required values are:

- `POSTGRES_PASSWORD`;
- `SECRET_KEY`;
- `BACKEND_CORS_ORIGINS`.

The remaining non-secret inputs and defaults are documented in
`.env.staging.example`. The operator records only a SHA-256 digest of the three
required values, not their contents. Preserve the exact configuration revision
outside Git if a later application rollback must reproduce it.

## Prerequisites

- a clean isolated worktree at the exact release commit;
- Git, PowerShell 7+, Docker Engine, and Docker Compose;
- populated staging configuration in process environment or an untracked file;
- exclusive operator ownership of Compose project `fitflow-staging`;
- local ports selected by `STAGING_BACKEND_PORT` and
  `STAGING_FRONTEND_PORT` are available.

Example invocation from the release worktree:

```powershell
pwsh ./scripts/staging/release.ps1 -Action deploy -Revision (git rev-parse HEAD)
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
pwsh ./scripts/staging/release.ps1 -Action redeploy -Revision (git rev-parse HEAD)
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

- clean target source and immutable full commit identity;
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
