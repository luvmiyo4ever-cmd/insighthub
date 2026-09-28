# ChatOps - Day 5

The bot exposes a local HTTP entrypoint through the `chatops` Compose profile.
It verifies Slack's raw request body, `X-Slack-Signature`, and
`X-Slack-Request-Timestamp` before parsing or handling an event. Requests older
than five minutes are rejected. A verified `app_mention` is put on the
dedicated Redis queue `arq:chatops`, deduplicated by Slack `event_id`, and is
then answered by `chatops-worker`. The HTTP event ACK never waits for an API,
Kubernetes, or Slack Web API request.

## Local deployment

1. Copy `slack-app-manifest.yaml.template`, replace the ngrok placeholder with
   its generated HTTPS host, then create or update the Slack App from that
   manifest. It declares only `app_mentions:read` and `chat:write`, and receives
   only the `app_mention` bot event.
2. Add `SLACK_SIGNING_SECRET` and the bot OAuth token (`SLACK_BOT_TOKEN`) to
   the repository-root local `.env` file. `chatops-bot/.env.example` is only
   the safe variable template; Compose reads the root `.env` for interpolation.
   Get the bot token from **OAuth & Permissions → Bot User OAuth Token** after
   reinstalling the app; it begins with `xoxb-`. Do not put it in an example,
   manifest, screenshot, or Git commit.
3. Run `docker compose --profile chatops up --build -d --wait`.
4. Check `http://localhost:8080/healthz`.
5. Start a local ngrok tunnel with `ngrok http 8080`, then configure the
   resulting HTTPS URL plus `/slack/events` in Slack. The signed URL challenge
   returns its challenge value.

## Supported questions

Mention the bot with one of these read-only questions (Vietnamese and English
variants are recognised):

- `api healthy?`
- `ingest count today?`
- `which pods failing?`

Ingestion count uses the fixed internal InsightHub API origin. API health calls
the Day 2 Prometheus MCP backend, and the pod intent only calls the Day 2
Kubernetes MCP backend. See [`deploy/chatops-mcp/README.md`](../deploy/chatops-mcp/README.md)
for the local read-only backend deployment and port-forward configuration. The
bot never turns the Slack message into an MCP URL, tool name, or argument.

The signing secret and ngrok credentials are local secrets; do not commit or
paste them into evidence. Transport doubles do not replace the required Slack
LIVE evidence. [Spec mục 9](../Running-Project-Specification-Student.md).

## Audit log

Every executed bounded tool call is appended as one UTF-8 JSON line to the
persistent Compose volume `chatops-audit`; the same compact record goes to
worker stdout. The record has `ts`, `user`, `tool`, safe fixed `args`,
`result`, and `approved`; it never contains secrets, Slack text, document
content, or raw MCP output.

Read it after an intent has run:

```powershell
docker compose --profile chatops exec -T chatops-worker cat /app/audit/chatops-audit.log
```

## Permission tiers and approved scale

Read-only intents are Tier 1 and run automatically. Tier 2 currently contains
one service-catalog action: `scale api to 1` through `scale api to 5`. The bot
creates an opaque, single-use Redis approval valid for 60 seconds, bound to the
requesting Slack user, `scale_api`, and the replica count. Only a follow-up
`confirm TOKEN` by that same user consumes the ticket and invokes the separate
mutator identity. Tier 3 destructive words are explicitly denied: no
destructive action is in this bot's service catalog.

The mutator source and namespace-scoped RBAC are in
[`deploy/chatops-mutator/mutator.yaml`](../deploy/chatops-mutator/mutator.yaml).
It can only `get` or `patch` the `deployments/scale` subresource named
`insighthub-api`; it cannot read Secrets or mutate another workload. It also
requires a separate HMAC secret, never the Slack signing secret.

Do not deploy or test the write path until a local secret is supplied. The
operator runbook in `deploy/chatops-mutator/README.md` creates the ignored
local secret and includes the explicit scale/recovery procedure.

## Tests

With the pinned dependencies installed, run the required suite from the
repository root:

```powershell
pytest chatops-bot/tests
```

For the reproducible local container check used by this project:

```powershell
docker run --rm -e PYTHONPATH=/app -v "${PWD}\chatops-bot\tests:/tests:ro" insighthub-do2603-chatops-worker:latest pytest -q /tests
```
