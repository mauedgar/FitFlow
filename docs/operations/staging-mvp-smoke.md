---
document_id: FF-OPS-STAGING-SMOKE-001
status: accepted_pending_implementation
machine_context: true
milestone: M4_STAGING_AND_BETA_READINESS
responsibility: R006
---

# Staging MVP vertical smoke

## Purpose

The smoke proves the deployed staging-like product through real HTTP interfaces,
not an in-process test client. API requests traverse the Nginx frontend proxy.
Direct backend requests are limited to liveness and readiness checks.

The demonstrated vertical is:

```text
frontend and API proxy
-> client login and Redis-backed refresh
-> class and concrete session visibility
-> membership-authorized booking
-> persisted client booking state
-> front-desk booking and capacity visibility
-> front-desk check-in
-> Redis-backed logout invalidation
```

## Fixture boundary

`backend/scripts/staging_smoke_seed.py` owns a reserved set of fixed UUIDs and
`m4-wave-b-*@example.com` identities. It refuses to run unless both conditions
hold:

- application configuration has `ENV=staging`;
- `FITFLOW_SMOKE_ALLOW_FIXTURE_RESET=1` is explicitly set.

Reset deletes and recreates only rows owned by those reserved IDs. It does not
truncate tables, drop the database, delete Compose volumes, or alter unrelated
records. The fixture password is intentionally repository-visible and must never
be used for a real account. The fixture is non-production test data.

Every run resets the fixture before making HTTP requests, so it does not depend
on a developer's existing database contents. Fixed identity, class, schedule,
session, and membership IDs make assertions deterministic. The concrete session
is recreated for local noon on the following day so booking remains valid.

## Run

First deploy the exact committed revision with the R005 procedure. In the same
process environment used by that deployment, run:

```powershell
$env:FITFLOW_SMOKE_ALLOW_FIXTURE_RESET = "1"
pwsh ./scripts/staging/smoke.ps1
```

Optional `-FrontendUrl` and `-BackendUrl` parameters support non-default local
ports. The script fails on any unexpected status, payload, state transition, or
missing fixture identity. It does not print access or refresh tokens.

Run the command twice to establish repeatability. A second pass must reset the
previous attended booking and reproduce the same full vertical from an empty
fixture-owned state.

## Stop conditions

Stop and return to CONTROL if:

- reset would touch data outside the reserved fixture IDs;
- the runtime is not explicitly configured as staging;
- a Product defect prevents the real HTTP vertical;
- the smoke would require external staging, a public URL, or real-user data;
- authentication, booking, or front-desk behavior must be bypassed to pass.
