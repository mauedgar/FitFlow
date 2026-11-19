---
document_id: FF-ISSUE108-REDIS-REGISTRY-20261118-001
status: review_required
issue: 108
baseline: 114@e5391ad3eb68fc27f84517fb811679fca3892536
integration: false
---

# JWT refresh ownership — bounded follow-up candidate

Separate stacked PR ownership; PR114 remains frozen and unmodified.
The original IR002 remains NO_RECOMMEND 0F/2A, unchanged.

New refresh registration compares signed unexpired JWT sub with the supplied
user, stores an opaque SHA256-derived key with positive expiry bounded by
signed JWT exp. Refresh verification checks the signed sub against the value
stored in Redis, not key existence alone. If a new opaque registration exists
with wrong owner, it fails closed without falling back to a legacy raw key.
Legacy raw keys are read-only for compatibility and are never written anew.
Logout rejects a refresh without matching registration.

This resolves the narrow Redis subject-binding invariant if independently
validated. **It does not repair revocation atomicity, unbounded historical
Redis data, logout ACK durability, already issued access tokens, family-scoped
revocation, raw JWT legacy blacklist keys, or persistence after Redis restart.**
Those are a high-risk separate session-revocation gate; no source integration
or staging approval is inferred from CI.

Only tests on disposable PostgreSQL15/Redis7 in GitHub Actions are authorized.
No retained data migration, secrets, dependency change, deployment, or merge.


## Independent A01 IR001 dispositions on 49b49f36 (historical, immutable)

Original `FITFLOW-C014-PR116-REGISTRY-A01-WEBINLINE-IR001-20261118-001` reports RECOMMEND_A01_SCOPED, 0 new findings / 2 advisories and explicitly NO_RECOMMEND for full Product. Original 8474 bytes SHA256 27df6da3ffb65edde8474534f3a228fbc3bff01b635de1666dd03050eedeb8a7; Git Transport custody blob e514afe991d6abed61e4b5ebea4306c0ebf6a809.

A01-A02 negative coverage is expanded here: forged JWT signature and expired signed refresh are both rejected even with synthetic preexisting Redis registration keys; the production guard has not been relaxed. An adjacent auth-service path now rejects soft-deleted users independently of the direct `get_current_user` pipeline, with negative HTTP check. This successor has not been independently reviewed or integrated.

A01-A01 legacy exposure still remains: historical raw JWT Redis key names may persist past JWT expiry. No automatic scan, forced deletion or retained-data migration is authorized. A competent deploy/legacy sunset decision must account for the longest signed legacy refresh expiry and inventory of existing keyspace; raw legacy records are never newly written by this candidate. New names are opaque with bounded TTL. **Current combined candidate:** A02 PostgreSQL session authority and modern
durable logout ARE IMPLEMENTED IN SOURCE on PR118. They are NOT_ACCEPTED,
NOT_DEPLOYED and not migrated into retained databases. The original Redis
legacy-surface limitations remain historic compatibility risks.
