# MH8 — structured audit file evidence

Collected: `2026-09-28T05:58:17Z` (UTC) in the local Docker Compose ChatOps
worker. No cloud resource, Slack token, signing secret, kubeconfig, document
content, or raw MCP response is recorded here.

## Persistent audit file

The `chatops-worker` Compose service mounts the named `chatops-audit` volume
at `/app/audit` and configures the worker with:

```text
CHATOPS_AUDIT_LOG_PATH=/app/audit/chatops-audit.log
```

Sources: `docker-compose.yml`, `chatops-bot/Dockerfile`, and
`chatops-bot/app/audit.py`.

## Readable JSON entry

After one fixed, read-only Prometheus health call, the file was read with:

```powershell
docker compose --profile chatops exec -T chatops-worker cat /app/audit/chatops-audit.log
```

Output:

```json
{"ts":"2026-09-28T05:58:17.691414+00:00","user":"mh8-verification","tool":"prometheus.query","args":{"query_id":"insighthub_up"},"result":"success","approved":true}
```

The same operation returned `InsightHub API healthy theo Prometheus MCP.` The
log preserves the required timestamp, user, tool, fixed safe arguments, result
summary, and approval flag. Each intent backend records both `success` and
sanitized `failure` outcomes. It does not preserve the Slack message, secret,
or raw MCP output.

`mh8-verification` is an explicit local verification label, not a claim that
this entry came from Slack. A live mention will append the actual Slack user id
through the same worker path.

## Regression check

The pinned worker image ran:

```text
Ran 19 tests in 0.018s
OK
```

`chatops-bot/tests/test_audit.py` covers both the structured record and its
append/read behavior from the configured audit file.
