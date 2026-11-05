---
document_id: FF-IR017-A13-BYTE-SAFE-OBSERVER-20261103-001
status: review_required
predecessor_commit: ea2633a10cb3341e9ee0d1b0f8b10914e7659072
predecessor_tree: eb6126b5a1a78808bb024d68652739dbaa1836c9
acceptance: false
---

# IR017 — safely characterizing invalid UTF-8 legacy Redis keys

The original independent [IR016](https://github.com/mauedgar/FitFlow/pull/68#issuecomment-6597785729)
reported 0 confirmed findings / 3 advisories A10/A12/A13, NO_RECOMMEND.
A13 additionally identified that historical non-UTF8 Redis keys could break
read-only characterization.

Repair: the metadata-only observer now opens its **own byte-safe Redis
client with decode_responses=False** after its explicit CLI read-only
flag/environment checks; no redis key or bearer value is decoded,
retrieved, logged, expired, changed or deleted by the observer.
Classification uses only an ASCII prefix comparison on raw bytes.
Connection timeout is bounded. Failures emit a single sanitized status.

New unit tests exercise invalid UTF-8 raw-key bytes and partial scans,
assert that the report exposes no secret-bearing names. A separate
integration fixture seeds/cleans an invalid UTF-8 key **only in isolated
loopback Redis with TESTING=true**, never retained staging or production.
That test is not a mutation by the observer and is not a cleanup grant.

A10 external-client rollout and all-network-partition guarantee remain
unqualified; A12 tested local topology still requires external ingress
host/provider evidence; A13 actual retained-store inventory and safe
retirement/last historical issuance remain unqualified.

No production Redis connection, retained key scan/delete, user credential,
staging host deploy or authority transfer in this repair. Revalidate all
CI against the next exact commit/tree, then original separate-context IR017.
No merge/close before 0 findings and 0 advisories and competent acceptance.
