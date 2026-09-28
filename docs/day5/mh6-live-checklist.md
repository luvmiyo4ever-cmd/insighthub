# MH6 — Slack three-intent live checklist

Status: **NOT VERIFIED as a complete set**. A prior Slack screenshot proves
the health response only. The remaining two live Slack threads must be
captured after the ChatOps worker and both MCP port-forwards are running.

In `#insighthub-ops`, use exactly one mention per thread:

1. `@InsightHub api healthy?` — expect a Prometheus MCP health response.
2. `@InsightHub ingest count today?` — expect document status totals.
3. `@InsightHub which pods failing?` — expect a namespaced Kubernetes MCP
   response; the current local lab can report `insighthub-baseline-warmup` as
   `Unknown`.

For each thread, save a screenshot that shows the channel, mention, bot reply,
and visible timestamp. Then capture the matching line from:

```powershell
docker compose --profile chatops exec -T chatops-worker tail -n 20 /app/audit/chatops-audit.log
```

Do not include tokens, signing secrets, raw MCP output, or document content in
the screenshots/evidence.
