# MH11 — three-minute screencast runbook

Status: **NOT RECORDED**. A Loom URL is required before MH11 can pass.

Record one continuous video, approximately three minutes, with no secret or
token on screen:

1. **0:00–0:25:** Show `docker compose --profile chatops ps` with bot and
   worker healthy; show ngrok forwarding only, not its auth token.
2. **0:25–1:35:** In `#insighthub-ops`, demonstrate the three MH6 mentions
   and their replies: health, today’s ingestion count, and failing pods.
3. **1:35–2:15:** Show the audit file command and one JSON record. Blur or
   avoid any sensitive terminal/environment panes.
4. **2:15–2:50:** Send `scale api to 2`, show the confirmation-only reply;
   only show the subsequent confirmation and actual scale after the separate
   mutator identity has been deployed and the safe recovery to one replica is
   also shown.
5. **2:50–3:00:** Show the 28-pass pytest result and the evidence directory.

Paste the final Loom URL below only after upload:

```text
LOOM_URL=NOT_RECORDED
```
