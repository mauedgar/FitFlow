---
document_id: FF-ISSUE49-SCHEMA-ARTIFACT-CONTRACT
status: review_required
issue: 49
owner: FITFLOW_CONTROL
baseline: develop@bff21562ab38124ff4c7383d156e59367218f66f
---

# Schema CI — authority and evidence (candidate)

## Scope and triggers
- Push runs only on develop for migration-related paths. Pull requests on
  migration-related paths and explicit workflow_dispatch may run on other
  exact candidate refs; they are intentionally permitted for disposable,
  read-only qualification. They are not authorizations to deploy or restore.
- The checked-out event SHA/tree, fixed PG15 loopback fixture, synthetic
  credentials, test profile, contents:read and no persisted Git credentials
  delimit ordinary CI. The same-process Alembic entrypoint checks the actual
  Settings URL, exact local owner/database, no query override and permitted
  revisions before migration. Separate negative fixtures verify raw-target
  denial and effective Settings mismatch with two allowed synthetic URLs.
  The Alembic environment uses the same imported Settings URL. This is not
  a network sandbox or attestation against malicious workflow/source changes.
- Direct SQL fixture operations use the explicitly defined synthetic service
  and test databases only. Real staging/retained databases remain forbidden.

## Schema source of truth
Canonical migrations and executable Product state govern schema; the raw
schema.sql is generated review evidence, not a second canonical schema and
never an automatic tracked commit. The raw random restrict/unrestrict key
pair is preserved. Compare two schema-only reads of the same fixture after
validating each directive pair and normalizing only key values in memory.
This proves same-database repeatability, not independent rebuild equivalence,
ORM drift detection, full migration correctness or production safety.
The normalizer recognizes column-zero directives from the pinned pg_dump
generator only. It is not a general SQL/psql framing or restore validator,
and arbitrary or corrupted SQL inputs are not admitted for this comparison.

The FK fixture requires the exact retained-child rejection message and
preservation of parent and child rows, rather than merely a generic
retained-data error. It does not claim a child-only nonnull FK with an empty
referenced parent, or prove exhaustive FK graph discovery.

FitFlow Control owns reconciliation of exact workflow run, job, subject
SHA/tree, raw ZIP/member digest and reviewer disposition. The independent
reviewer evaluates the frozen scope; acceptance/integration requires competent
Product authority and native protections. On mismatch, keep the original
failed/partial evidence, stop conflicting effects and repair only in a new
authorized candidate; never overwrite the original dump or blindly rerun.
No schema SQL is restored or applied by this workflow. Tracking schema.sql,
changing permissions, retained migrations or deployment require a separate
competent decision.

## Original and scope
IR001 original [0F/4A](https://github.com/mauedgar/ts-execution-transport/blob/33cc837cbd5de5bf7ee15108fdf1239c8b507b58/results/FITFLOW-ISSUE49-WORKFLOW-IR001-20261125-001/ORIGINAL.md)
is immutable. Accepted PR113 original run44227579962/job134544430516
SUCCESS, artifact14393855714 raw ZIP SHA256
384c835b3cb195ff4d3288185df947c399215f5a222240a70c382e92168401ca,
subject d5fe2df72cad1fab4941bdd7dc789b8ccbccf0f8/tree
3199e76a9b7fa8661c3b03febbfb04bc78e8444d, SQL SHA256
25205106e850fc156436f09308371b3684fceb636677762f3cc1c1a79dedc6fc.
Native setup logs explicitly confirmed uv0.13.6. Original evidence not
transferred as PASS to this successor. A01/A04 authority and limits
documented; A02/A03 bounded workflow hardening requires original successor
CI and independent review. IR002 0F/3A is preserved at
[its original](https://github.com/mauedgar/ts-execution-transport/blob/53f31c61bf39e8df1adddd7501f9613b08eab1ab/results/FITFLOW-PR121-ISSUE49-IR002-SCHEMA-SUCCESSOR-20261125-001/ORIGINAL.md).
SA01 clarifies the generator-only comparison boundary; SA02 adds a distinct
effective-Settings negative fixture; SA03 requires the named child denial.
Successor CI and independent review remain required; no historical PASS
transfer. #47 quality and #108 security remain separate.
