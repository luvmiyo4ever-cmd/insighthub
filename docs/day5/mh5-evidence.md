# Day 5 — MH5 Slack configuration evidence

Status: **incomplete evidence set**. This file records only observations that
are available in the repository or were supplied in the current chat; it does
not claim that Slack configuration is verified until the missing screenshots
are captured.

## 1. Bot invited to the operations channel

- Evidence: [`bot-invited-insighthub-ops.png`](bot-invited-insighthub-ops.png)
- Captured: `2026-09-28T11:25:05+07:00` (local file timestamp)
- Observation: Slack displays `InsightHub was added to #insighthub-ops` and the
  `InsightHub` app is listed under **Agents & apps**. The screenshot also shows
  an `@InsightHub api healthy?` mention.
- Scope: this proves channel membership only. It does **not** prove an Event
  Subscription delivery or a bot reply.

## 2. Public endpoint

- User-provided ngrok endpoint:
  `https://reason-humility-canal.ngrok-free.dev/slack/events`
- The corresponding local target reported by ngrok is `http://localhost:8080`.
- Screenshot of the ngrok console or inspection UI: **not yet stored**.

## 3. Slack App configuration — required before MH5 can be claimed

Capture and add a screenshot that visibly shows all of the following:

- **OAuth & Permissions → Bot Token Scopes** includes `app_mentions:read` and
  `chat:write`.
- **Event Subscriptions** is enabled, the Request URL is **Verified**, and
  **Subscribe to bot events** includes `app_mention`.
- The Request URL is exactly the HTTPS ngrok endpoint above.

Do not include the Slack signing secret, bot token, ngrok authtoken, or webhook
URL credentials in screenshots or this document.
