# Day 4 controlled incident lab

The API chaos hooks are disabled by default. Enable them only in the local
cluster, run one incident at a time, and restore the values immediately after
capturing the Prometheus evidence. Do not use these scripts against a shared
or production cluster.

Prerequisites:

1. Prometheus has at least 120 samples (one hour at the configured 30-second
   interval) for the relevant recording metric.
2. The API is available through a local port-forward, normally
   `http://127.0.0.1:18000`.
3. For latency/error cases, enable the double-gated API hook temporarily:

   ```powershell
   helm upgrade insighthub charts/insighthub -n insighthub --reuse-values `
     -f charts/insighthub/values-observability-local.yaml `
     -f charts/insighthub/values-day4-chaos-local.yaml `
     --set-string api.env.DAY4_CHAOS_ENABLED=true `
     --set-string api.env.DAY4_CHAOS_LLM_DELAY_SECONDS=5
   ```

For a queue incident, keep the worker running so its queue-depth metrics stay
scrapeable. Enable the worker-only bounded delay instead of scaling the worker
to zero:

```powershell
helm upgrade insighthub charts/insighthub -n insighthub --reuse-values `
  -f charts/insighthub/values-day4-chaos-local.yaml `
  --set-string worker.env.DAY4_CHAOS_ENABLED=true `
  --set-string worker.env.DAY4_CHAOS_WORKER_DELAY_SECONDS=30
```

Run `inject-llm-latency.ps1`, `inject-queue-backlog.ps1`, or
`inject-http-errors.ps1`. Capture the baseline, active alert, and recovery
timestamps before writing the corresponding RCA. Restore the hook with a Helm
upgrade using `values-day4-chaos-local.yaml` alone.

Do not use a scaled-to-zero worker as queue-alert evidence: the queue gauge is
emitted by the worker, so Prometheus would only retain its last stale sample.
