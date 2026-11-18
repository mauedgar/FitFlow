---
document_id: FF-ISSUE108-JWT-PURPOSE-ISOLATED-20261118-001
status: candidate_not_accepted
issue: 108
baseline: develop@276481de41f6829e8dd7beed79127e13237b5dcb
integration: false
---

# Issue 108 — JWT purpose boundary, isolated candidate

This candidate is based on canonical FitFlow CPython3.15.2 develop after PR113.
Developer delegated JWT-purpose ownership away from diverged PR107 into a new
isolated candidate, without modifying or reusing PR107/109/111's historical
attempts, commits, reviews, session revocation and frontend changes.

Emitters set signed, nonoverridable `token_use=access` or `token_use=refresh`.
Refresh emitters strip any caller-supplied role. Both bearer guards reject
refresh JWT, including untyped legacy refresh. Refresh and logout reject
access JWT. Unknown explicit purposes, absent/expired `exp`, invalid subject
and signed role on legacy refresh are invalid. Untyped legacy access requires
a signed nonempty role and live expiration; untyped legacy refresh has no
role and remains subject to existing Redis registration/blacklist.

Refresh now resolves a current, active, non-soft-deleted account by UUID from
PostgreSQL before issuing a typed access JWT with that account's current role.
Never trust client-provided refresh role. No token migration, credential reset
or retained Redis/PostgreSQL effect occurs in this candidate. The existing
logout API still requires bearer authentication: authoritative durable
revocation, Redis TTL/opaque keys, `sid`, SPA logout recovery and pending ACK
remain separate unaccepted Product responsibilities under PR107.

Only disposable PostgreSQL/Redis and synthetic identities may be used for
HTTP validation. Require final-head Python3.15.2 CI and independent full
security review with explicit 0F/0A disposition before acceptance. Neither
historical PR107 CI nor this candidate's source is an acceptance grant.
Staging, deployment, secrets, migrations and ruleset changes are excluded.
