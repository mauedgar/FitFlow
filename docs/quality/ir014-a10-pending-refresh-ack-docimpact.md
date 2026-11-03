---
document_id: FF-A10-ACK-V1-20261103-001
status: review_required
authority: FitFlow Product / user-authorized continuation from PR64 IR013
predecessor_sha: 166fed231c8f45a01e3e914c619e495d31f0eaa5
acceptance: false
---

# IR014 A10 — negotiated pending-refresh acknowledgement candidate

## Scope and semantics

PR64 IR013: 0 confirmed findings, 3 advisories (A10/A12/A13), NO_RECOMMEND.
This is **not** Product acceptance and cannot transfer PR64's CI or independent review.

The active React login (and exported legacy helper) now sends
`X-FitFlow-Refresh-Ack: v1`, receives a token pair, and **acknowledges before
publishing it to sessionStorage/UI**. The backend stores a negotiated refresh in
a distinct HMAC-addressed Redis pending key with at most **120 seconds** TTL,
never in the active set until a signed, authenticated, user-bound /auth/ack.
ACK is atomic/idempotent for duplicate/lost ACK replies and promotes a credential
for no longer than its original signed expiration. A pending token cannot call
/auth/refresh; /auth/logout deletes pending and active keys and blacklists.
No token is logged or written into query parameters.

A lost **token-pair response** therefore leaves only a short pending entry.
A lost **ACK response** can be safely retried. Invalid, wrong-user and expired
ACK requests must not activate the token. These claims require exact CI and IR.
The existing headerless login remains unchanged for external/older clients.
**This is an opt-in bounded mitigation, not full closure of A10:** legacy
headerless clients may still have orphaned tokens up to their configured signed
TTL. A versioned migration/rollout decision plus evidence of client adoption are
required before any universal 0A assertion or mandatory ACK deployment.

## Other advisories and ownership

A12 stays OPEN: repository staging has Nginx proxying /api/ and also directly
publishes backend. Real proxy peer/forwarded trust, rate limiter shared-IP
fairness and recovery must be proven on a disposable, exact topology without
changing production ingress or secrets.

A13 stays OPEN: do not remove signed pre-jti raw Redis compatibility without
evidence of maximum historical expiry and production migration approval.
No production Redis scan, deletion, secret, staging deploy or database migration.

Required gates: full exact GitHub Actions (PG15/Redis7 Python3.11/12/13,
Ruff/Pyright, frontend Node22, Chrome mounted and bcrypt/schema), dedicated
pending/active TTL/ACK negative tests, original independent WEB_INLINE IR014
on frozen commit/tree. No merge or acceptance if any finding/advisory persists.
