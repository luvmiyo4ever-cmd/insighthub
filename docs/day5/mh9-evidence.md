# MH9 — permission tier evidence

Collected: `2026-09-28T06:11:50Z` (UTC), local Docker Compose worker. This
document does not contain a confirmation token, Slack token, signing secret,
or Kubernetes credential.

## Implemented policy

| Tier | Policy | Enforcement source |
|---|---|---|
| Read | Existing three operational intents execute automatically. | `chatops-bot/app/worker.py`, `app/operations.py` |
| Write | Only `scale api to 1..5` is allowed; a one-time 60-second approval is bound to Slack user, `scale_api`, and replicas. | `chatops-bot/app/permissions.py`, `app/approvals.py` |
| Destructive | No destructive action is in the service catalog; delete/destroy/wipe/drop requests are explicitly denied. | `chatops-bot/app/permissions.py`, `app/worker.py` |

The mutator has its own ServiceAccount and a namespace-scoped Role that only
allows `get`/`patch` on `deployments/scale` for `insighthub-api`.
Source: `deploy/chatops-mutator/mutator.yaml`.

## Non-mutating live worker check

The worker was asked to create an approval for `scale api to 2`. The returned
opaque confirmation token was deliberately not retained. The audit file
contained:

```json
{"ts":"2026-09-28T06:11:50.513497+00:00","user":"mh9-verification","tier":"write","action":"scale_api","args":{"replicas":2},"result":"pending","approved":false}
```

This demonstrates that requesting a write action does not mutate the
deployment. The test identity is local-only, not a Slack user.

## Static checks

`kubectl apply --dry-run=client -f deploy/chatops-mutator/mutator.yaml`
validated all six objects: ServiceAccount, Role, RoleBinding, Deployment,
Service, and local NetworkPolicy.

The test suite includes request parsing, confirmation-only execution,
wrong-user/expired rejection, destructive denial, and mutator raw-body HMAC
validation. See `chatops-bot/tests/test_permissions.py`,
`test_worker_permissions.py`, and `test_mutator_auth.py`.

An integration check against the local Redis approval store also confirmed that
a different identity cannot consume or invalidate the owner ticket; the owner
could consume it afterwards. The test output was
`approval-remains-bound-to-owner` and did not expose the generated token.

## Local runtime verification

The local `chatops-mutator` ServiceAccount, Role, RoleBinding, Deployment,
Service, NetworkPolicy, code ConfigMap, and independently created Secret were
applied in the `docker-desktop` `insighthub` namespace. The mutator was Ready
and its RBAC was verified as follows:

```text
can patch deployment/insighthub-api --subresource=scale: yes
can patch deployment/another-api --subresource=scale: no
```

After the mutator HMAC identity and local port-forward were verified, two
separate approvals ran through the real worker path:

```text
2026-09-28T06:45:45Z  scale_api replicas=2  pending -> kubernetes.deployments_scale success
desired replicas after scale-up: 2

2026-09-28T06:45:49Z  scale_api replicas=1  pending -> kubernetes.deployments_scale success
desired replicas after recovery: 1
deployment "insighthub-api" successfully rolled out
```

The exact JSON audit records are retained in the persistent worker audit file;
they include no token or secret. Earlier failed attempts are intentionally
retained there as well: one HMAC mismatch and one stale port-forward, both
produced no deployment change and were resolved before the successful run.

## Status

**PASS for local MH9 scale verification.** The identity label
`mh9-live-verification` denotes a controlled local worker test, not a Slack
user. Capture a Slack `scale api to 2` / `confirm TOKEN` thread separately if
you need Slack UI evidence; always use a new approval to restore the prior
replica count.
