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
