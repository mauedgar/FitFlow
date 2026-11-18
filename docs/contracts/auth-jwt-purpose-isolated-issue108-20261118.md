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


## IR001 review disposition — residual coverage and inherited registry boundary

IR001 on exact earlier HEAD `85245095b27fb21420e7847b49390e26d0e6444f`
returned immutable `NO_RECOMMEND / 0F / 2A` (not a source acceptance).
The successor adds isolated PostgreSQL HTTP cases for active-but-soft-deleted
users and stale signed role with a current unprivileged database role; and
strict GITHUB_ACTIONS-only real disposable Redis7 cases for unregistered
refresh rejection, registered positive refresh, blacklist denial, real logout
204 and denial after revocation, with per-credential cleanup. The new tests
do **not** claim to prove atomic logout after Redis crashes or a client ACK loss.

**Separate inherited Redis trust boundary:** `token_store.is_refresh_token_valid`
currently checks token-key existence but does not compare its stored user-id
value with signed JWT `sub`. That behavior predates this JWT-purpose candidate
and is neither repaired nor declared secure here. Binding Redis registration
to a persisted owner, plus opaque keys/TTL/SID revocation and durable logout
ACK, require their own competent scope/implementation and security review;
no retained Redis change or credential migration is authorized. This
candidate's success must not be described as complete refresh registry
ownership integrity or full remote-session revocation. Issue #108 stays OPEN
until those separately authorized security responsibilities are reconciled.
