---
document_id: FF-IR015-A10-F01-ACK-NETWORK-RETRY-20261103-001
status: review_required
authority: FITFLOW_CONTROL / Developer approved autonomous repair of IR014
predecessor_commit: f4faf71afc56e6248110373664c3c2d050583bc5
predecessor_tree: 645cc823128a50506c8cbd9be8d3c9228db4faf6
acceptance: false
---

# IR015 — A10/F01 lost HTTP 204 ACK response repair

The original independent [IR014](https://github.com/mauedgar/FitFlow/pull/66#issuecomment-6596909924)
reported **FAIL / NO_RECOMMEND (1F/3A)** on PR66. It found that a server
ACK can activate Redis even when the 204 response is lost, while the SPA
throws, discards the token pair, and cannot revoke it.

The shared frontend `acknowledgeRefreshDelivery(pair)` now retries only
transient HTTP transport or server failures up to three times, with an
individual 2500 ms request timeout and short bounded delays. Every retry
uses the same issued access+refresh pair; it cannot invoke another login.
The backend ACK is idempotent and cannot extend the JWT lifetime.

If all attempts fail or a permanent HTTP error occurs, the frontend
performs a best-effort compensating authenticated `/auth/logout` of
**the same token pair**, then returns the original failure. Server
unreachability cannot establish revocation. This is a bounded F01 repair,
**not** universal A10 closure for all possible network partitions.

The mounted Chrome test now simulates the first ACK being accepted by the
synthetic API while its HTTP response is destroyed. It verifies a second
ACK carrying the exact same pair, only one token-pair issuance, actual
React login, existing refresh/rehydrate and logout scenarios. This is
frontend browser behavior against synthetic API, **not** actual
Nginx/FastAPI/Redis staging. Existing backend disposable Redis tests
already prove ACK idempotence and pending/active transitions.

A10 legacy headerless immediate activation remains unresolved; so do A12
deployed proxy/shared-IP recovery and A13 historical Redis key migration.
No production Redis, network ingress, DB, secrets, dependencies or staging
services are changed. Full CI on the new exact commit/tree, independent
WEB_INLINE IR015, 0F/0A and competent acceptance are still required.
