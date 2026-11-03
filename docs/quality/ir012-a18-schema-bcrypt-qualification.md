---
document_id: FF-IR012-A18-QUALIFICATION-20261103-001
status: candidate_for_independent_review
authority: FITFLOW_CONTROL / user_authorized_A18_verification_A10_A12_preparation
source: https://github.com/mauedgar/FitFlow/pull/63#issuecomment-6595057288
acceptance: false
merge_authorized_without_0F0A: false
---

# IR012 — A18 evidence closure candidate; A10/A12/A13 pending

## Frozen source, authority and non-transfer

Predecessor [PR63 IR012](https://github.com/mauedgar/FitFlow/pull/63#issuecomment-6595057288)
on immutable commit `41662605790a4b7c76766969b1c97d52f1a44f30`,
tree `deec3c63f62672f2410cb8350185532b1980b295`,
returned **0 findings / 4 advisories (A10, A12, A13, A18) /
NO_RECOMMEND**. CI PASS from PR63 does **not** transfer to a successor.

## A18a — exact schema archive independently inspected by Control

Original GitHub Actions workflow `41574233520` generated artifact
`fitflow-schema-sql-41574233520`, ID **13202841670**,
reported immutable GitHub artifact digest:

`sha256:22c85ff4ca030fa54edc2e328c17c60326088c200b2ccdd061022f2cc0fd7540`

Using the GitHub connector's **download_workflow_artifact** action,
Control downloaded the actual ZIP bytes and inspected them read-only,
without creating a database or executing the SQL. Independently
computed the ZIP SHA256 as exactly the GitHub-reported digest.

The ZIP was valid, with **three entries** only:
- `schema.sql`: 14,182 bytes, SHA256
  `97af618c8bde45796e570de648f45782c41227300fadaf6ce3034782faad74e4`.
- `schema.sha256`: records the same SQL SHA256, with filename
  `schema.sql`; exact match against uncompressed SQL bytes.
- `subject.txt`: records exact
  `subject_sha=41662605790a4b7c76766969b1c97d52f1a44f30` and
  `subject_tree=deec3c63f62672f2410cb8350185532b1980b295`.

Semantic read-only inspection of uncompressed `schema.sql`:
PostgreSQL 15.19 pg_dump from server/client 15.19, **10 CREATE TABLE**
(alembic_version, bookings, class_schedules, class_sessions, clients,
gym_classes, memberships, persons, teachers, users), **8 enum types**,
**11 indexes**, **24 constraints**. No `COPY` or `INSERT` data statements;
no `SECRET_KEY` string. Raw dump's matching randomized
`\\restrict` / `\\unrestrict` keys remained intact (not rewritten).
This evidence proves an inspected **schema-only artifact**, not runtime
migration correctness or compatibility with a production database.

The reviewer must obtain and verify the original artifact or otherwise
explicitly qualify its confidence; it must **not** treat this document
alone as independent cryptographic verification.

## A18b — extend reverse Passlib checks to every supported native Python

The prior `.github/workflows/issue43-bcrypt-verify.yml` had two reverse
compatibility steps gated `if: matrix.python == '3.11'`; hence
Python3.12/3.13 ran native bcrypt 4.3 vectors but not *cross-interpreter*
reverse checks against legacy Passlib.

The candidate retains **native bcrypt==4.3.0** as the only Product
password-hash library and retains `passlib` excluded from `uv.lock`.
It keeps the existing 3-version matrix, but for **each** Python
3.11/3.12/3.13 job:
1. Install only a disposable Python **3.11.17** interpreter using
   the existing pinned uv tool inside the ephemeral CI runner.
2. Create `/tmp/issue43-legacy` from that interpreter and install
   isolated, explicitly pinned `passlib==1.7.4` and `bcrypt==3.2.2`.
3. Produce and verify Passlib 2a/2b/2y synthetic hashes/negative
   vectors in that legacy interpreter; verify them with the **matrix's**
   actual native FitFlow bcrypt runtime.
4. Create new bcrypt 4.3 hashes in that matrix runtime and verify them
   with the isolated Python3.11 Passlib runtime (including expected
   72-byte legacy alias behavior), checking wrong passwords are denied.

The ephemeral legacy interpreter is intentional: Passlib 1.7.4 is
**not** a supported Product dependency on Python 3.12/3.13, and must
not be installed into FitFlow's runtime or used to generate real tokens.

Required evidence: per-version job logs with both
`ISSUE43_CROSS_ENV_LEGACY_COMPAT_PASS 15` and
`ISSUE43_CROSS_ENV_NATIVE_TO_LEGACY_PASS 6`, exact SHA/tree, full
CI and bcrypt, schema, structure, Chrome gates; independent source
review to decide whether A18 can be closed.

## A10 — bounded candidate design, NOT approved implementation

Refresh issuance registers the signed credential before HTTP delivery.
A client that never receives it cannot trigger its revocation.
A **possible** versioned redesign would register a short-lived *pending*
session that cannot refresh access until the client acknowledges the
received credential via a separately authenticated endpoint, with
bounded TTL and deterministic replay/duplicate/lost-response tests.
This is a prospective Product/API decision: it changes auth semantics,
requires compatibility/rollback and Redis transaction safety analysis.
**No A10 implementation or risk acceptance is authorized by this
qualification-only change.** Existing default 7-day refresh lifetime
remains a documented ceiling *only under default configuration*.

## A12 — bounded operational qualification plan, NOT deployment PASS

For the repository's current Compose staging topology, backend/frontend
are exposed via ports, **without a specified reverse proxy, trusted
upstream source list, external ingress, or real shared-IP recovery
policy**. The existing synthetic tests demonstrate that the in-process
FastAPI request uses ASGI `request.client.host` and rejects spoofed
X-Forwarded-For/X-Real-IP/Forwarded headers, and that staging rejects
`TESTING=true`. Redis Lua atomic caps have synthetic tests.

Before declaring deployed A12 PASS, obtain a competent **exact host,
network topology and ingress/proxy-header trust configuration** and
bounded permission to observe/validate it. Specify trusted peer CIDRs,
header translation and anti-spoof boundary (or explicitly no proxy),
real anonymous/legitimate shared-IP scenarios, account lockout window,
retry-after and recovery. Don't trust arbitrary forwarded headers,
introduce proxy authentication in docs alone, or operate against real
accounts. No staging services or network configuration were changed.

## A13 — preserve backward-compatible legacy Redis state

Pre-jti, signed refresh tokens can still have raw-token Redis keys
until expiry. Do not assume the 7-day modern default is the longest
historical lifetime; production configurations and last signed legacy
issuance are not independently established. No production key scanning,
retirement, migration, deletion, or shortening of token validity was
authorized.

## Exact-candidate review and integration boundary

This is a repair/evidence successor, **not** Product acceptance.
Run the entire original GitHub Actions suite on its exact commit/tree;
the new bcrypt compatibility matrix is an additional necessary gate.
Conduct original WEB_INLINE independent review with evidence
readback. The user conditionally authorized acceptance and integration
only for **0 findings, 0 advisories**, with current competent
merge preconditions checked. Remaining A10/A12/A13 are **not**
automatically disposed by A18 evidence.
