# MH7 — local MCP backend and audit evidence

Collected: `2026-09-28T05:25:03Z` (UTC) on the local `docker-desktop`
cluster. No cloud resource, kubeconfig, bearer token, Slack token, or document
content is included here.

## Backend deployment

Command:

```powershell
kubectl -n insighthub get deployment chatops-kubernetes-mcp chatops-prometheus-mcp
```

Output:

```text
NAME                     READY   UP-TO-DATE   AVAILABLE
chatops-kubernetes-mcp   1/1     1            1
chatops-prometheus-mcp   1/1     1            1
```

Source: `deploy/chatops-mcp/kubernetes-mcp.yaml` and
`deploy/chatops-mcp/prometheus-mcp.yaml`. Both are ClusterIP-only. The
Kubernetes MCP deployment uses `insighthub/mcp-readonly`, server-side
`read_only = true`, and exposes only `pods_list_in_namespace`; the Prometheus
MCP deployment has no Kubernetes API token.

## Kubernetes RBAC and call

Command:

```powershell
kubectl -n insighthub auth can-i list pods --as=system:serviceaccount:insighthub:mcp-readonly
```

Output: `yes`

The worker called the fixed tool and namespace (not Slack-controlled input):

```text
{"ts":"2026-09-28T05:24:49.889724+00:00","user":"mh7-verification","tool":"kubernetes.pods_list_in_namespace","args":{"namespace":"insighthub"},"result":"success","approved":true}
Pod cần chú ý theo Kubernetes MCP:
- `insighthub-baseline-warmup`: Unknown (0/1 Ready)
```

Sources: `tools/mcp/day2/mcp-readonly-rbac.yaml`,
`chatops-bot/app/mcp.py`, `chatops-bot/app/operations.py`, and
`chatops-bot/app/audit.py`.

## Prometheus call

The worker called the fixed health query through the Prometheus MCP backend:

```text
{"ts":"2026-09-28T05:25:03.471455+00:00","user":"mh7-verification","tool":"prometheus.query","args":{"query_id":"insighthub_up"},"result":"success","approved":true}
InsightHub API healthy theo Prometheus MCP.
```

The query itself is fixed in source as
`up{job=~"insighthub-api|insighthub-worker"}`; audit stores the query id, not
the full backend response.

## Regression tests

Executed in the pinned ChatOps worker image:

```text
Ran 17 tests in 0.017s
OK
```

Coverage includes fixed namespaced Kubernetes tool selection, fixed
Prometheus query selection, and structured audit records in
`chatops-bot/tests/test_operations.py` and `chatops-bot/tests/test_audit.py`.

## Scope and remaining live check

This verifies both MCP backends and the audit record from the local worker;
the verification identity `mh7-verification` is a local test label, not a
Slack user. It is not evidence that a Slack mention has traversed this MH7
path. Capture that separately by mentioning the bot in `#insighthub-ops` and
then saving the resulting Slack thread plus worker log record.
