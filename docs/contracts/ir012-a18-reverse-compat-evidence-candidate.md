---
document_id: FF-IR012-A18-EVIDENCE-20261103-001
status: review_required
authority: user_approved_A18_qualification_and_A10_A12_preparation
predecessor: https://github.com/mauedgar/FitFlow/pull/63#issuecomment-6595057288
product_acceptance: false
integration_authorized_conditionally_only_if_exact_0F0A: true
---

# IR012 successor — A18 reverse bcrypt/Passlib qualification and evidence boundary

## Competent frozen predecessor

PR63 independent WEB_INLINE IR012 reviewed commit
`41662605790a4b7c76766969b1c97d52f1a44f30`,
tree `deec3c63f62672f2410cb8350185532b1980b295`,
SOT v5.3 and returned **0 findings / 4 advisories / NO_RECOMMEND**.
The user's conditional acceptance/integration authorization applies only
to a competent current independent **0 findings + 0 advisories** candidate,
never to this predecessor or its CI alone.

## A18 sub-dependency 1 — independently inspected schema archive

Control downloaded the exact [PR63 schema artifact #13202841670](https://github.com/mauedgar/FitFlow/actions/runs/41574233520)
through GitHub and unpacked it locally, verifying:
- ZIP size 2702 bytes and SHA256
  `22c85ff4ca030fa54edc2e328c17c60326088c200b2ccdd061022f2cc0fd7540`,
  equal to GitHub artifact digest.
- Exactly `schema.sql`, `schema.sha256`, `subject.txt`.
- `subject.txt` names exact PR63 commit/tree; independent
  `schema.sql` SHA256
  `97af618c8bde45796e570de648f45782c41227300fadaf6ce3034782faad74e4`
  equals the embedded `schema.sha256`.
- PostgreSQL/pg_dump 15.19, 10 expected tables, 11 indexes,
  24 ADD CONSTRAINT, matching restrict/unrestrict guard and dump footer.
- [Published A18 evidence-only receipt](https://github.com/mauedgar/FitFlow/pull/63#issuecomment-6595179644).

This validates artifact ZIP content and integrity for **PR63 only**.
It is not a PostgreSQL restore or proof of a deployed schema.
A future candidate's newly generated archive must be bound to its own
immutable commit/tree before any new exact-candidate claim.

## A18 sub-dependency 2 — reverse compatibility across target Python

The existing `.github/workflows/issue43-bcrypt-verify.yml`
had native bcrypt unit vectors on Python3.11,3.12,3.13, but generated
Passlib 1.7.4/bcrypt3.2.2 historical vectors and reverse-verified new
hashes exclusively on Python3.11. It was previously legitimate to
call these **scoped skips**, but not cross-runtime proof.

The updated compatibility matrix:
1. Retains the previously pinned supported target Python3.11/3.12/3.13
   with native bcrypt4.3.0 and existing synthetic tests.
2. Captures each target interpreter's **absolute path** before adding
   a second, pinned Python3.11 interpreter in the **same ephemeral
   runner**, solely for legacy isolated Passlib 1.7.4/bcrypt3.2.2.
3. For each target Python, generates 15 historical Passlib hashes on
   isolated Python3.11 (2a/2b/2y, empty, Unicode, exact and overlength
   boundary cases) and checks correct/incorrect passwords using
   that target's native bcrypt security implementation.
4. For each target Python, generates 6 native bcrypt4.3.0 hashes,
   verifies them using isolated old Passlib and checks wrong-password
   and 72-byte legacy suffix behavior.

The historical interpreter **never becomes a Product dependency**.
The Product dependency lock, database schemas, migrations, backend
implementation, real credentials and Redis are unchanged. Output log
markers `ISSUE43_LEGACY_VECTOR_GENERATION_PASS`,
`ISSUE43_CROSS_ENV_LEGACY_COMPAT_PASS`,
`ISSUE43_NATIVE_BCRYPT43_VECTOR_GENERATION_PASS`,
`ISSUE43_CROSS_ENV_NATIVE_TO_LEGACY_PASS` must occur independently in
each target matrix job. Exact CI, source review and original independent
review still required. If a target fails, record the real failure and
repair it rather than suppressing a supported matrix item.

## Pending A10 / A12 / A13 decisions — NOT approval or closure

**A10 MEDIUM:** `/auth/token` registers a signed refresh before HTTP
delivery and its default expiry is seven days. Lost HTTP response may
strand a token unseen by the client until signed TTL. Propose a
versioned issuance acknowledgment/idempotency protocol with bounded
unacknowledged-token lifetime, negative tests for partial delivery,
refresh and logout interactions, and legacy-client compatibility, or
an explicit, accountable Product risk decision. No protocol change,
risk acceptance or token revocation claimed by this candidate.

**A12 MEDIUM:** in-process tests validate ASGI peer selection against
spoofed forwarding headers, and Redis Lua atomic limits and staging
`TESTING=false` are tested separately. The repo's staging Compose
publishes localhost-forwarded ports but defines **no real ingress
proxy, trusted proxy peer list, shared-IP policy or recovery mechanism**.
A trustworthy operational qualification must first designate an
actual supported topology and trusted peer boundary, then test it
without trusting arbitrary Forwarded headers. No unobserved
production topology was fabricated or deployed.

**A13 LOW:** signed pre-jti legacy refresh entries still use raw Redis
compatibility lookups. The currently configured refresh lifetime is
seven days by default, but the actual longest historical expiry and
real stored-key presence are unknown. No raw key migration,
production Redis inspection, deletion or compatibility retirement
is authorized. Preserve read-only legacy compatibility until a
separate, evidenced Product cutoff.

### Required gates

Qualify the exact successor with all existing GitHub Actions matrix
and the Chrome mounted E2E, as well as this expanded bcrypt
compatibility matrix. Download/unpack any *new* schema artifact for
the exact successor before claiming A18 full evidence closure.
Request original separate-context WEB_INLINE IR013 on frozen commit/tree
only after CI; independent reviewer must assess inherited A10/A12/A13
and any residual findings/advisories. Never automatically accept
or merge without current independent 0F/0A and competent merge
preconditions.
