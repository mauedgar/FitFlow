---
document_id: FF-IR016-A10-A12-A13-PREFLIGHT-20261103-001
status: review_required
predecessor_commit: 3648bd5d6ed2064662c703b0150d8387f8dc9115
acceptance: false
---

# IR016 — staged ingress, negotiated ACK policy, legacy Redis inventory

Predecessor [IR015](https://github.com/mauedgar/FitFlow/pull/67#issuecomment-6597103871):
**0 new findings / 3 advisories A10/A12/A13, NO_RECOMMEND**, on the
frozen PR67 candidate. This successor requires new exact CI and IR.
No prior PASS transfers.

**A10:** Staging Compose now chooses `REFRESH_ACK_POLICY=required` and
rejects headerless login before a user or Redis lookup (HTTP 426);
first-party SPA and staging smoke negotiate ACK v1. Production/default
application remains explicitly `compatible` until a controlled external
client inventory, release version, observed rollout and acceptance;
the legacy flow is NOT prematurely disabled. A complete network
partition still cannot prove revocation after terminal retries.

**A12:** Nginx overwrites untrusted `X-Forwarded-For`, strips
`Forwarded`, and sets `X-Real-IP`. Staging Compose has a fixed
**isolated edge subnet** and exact static trusted frontend peer IP;
Uvicorn trusts only that validated IPv4, never `*` or a network-wide
CIDR. Frontend is the sole edge ingress; backend remains accessible on
**127.0.0.1 only** for existing R005/R006 health and smoke. Docker
network subnet and peer must be checked for conflicts and adapted as a
reviewed configuration pair, not silently published to a public host.
No public TLS/DNS/ingress provider is implied. Docker-based disposable
topology CI is justified because the subject is actual
Nginx-to-Uvicorn peer trust, not an in-process HTTP transport. It
owns only a uniquely named synthetic Compose project and disposable
DB/Redis volumes, never live staging or production.

**A13:** Historical `bb6ead6d` Redis key writes had NO expiration.
Default JWT validity was seven days but runtime overrides may differ.
A bounded read-only observer classifies legacy raw-key presence and TTL
without printing bearer key names or values; no live Redis connection
was made by Control. An inventory of an actual retained store, last
issuance and approved cleanup/retention remain pending. Expired JWTs
are rejected regardless of persistent orphaned Redis keys. The
observer never performs `SET`, `DEL`, `EXPIRE` or obtains values.

**Gates:** exact candidate, isolated topological proof, full existing
PG15/Redis7 Python3.11/12/13, Ruff, Pyright, frontend and Chrome CI;
negative failure cases, review of startup/release/smoke configuration,
independent original WEB_INLINE IR016, then explicit Product decision
for any remaining A10/A12/A13. No automatic merge/close/production
state or claims of 0A from missing external evidence.
