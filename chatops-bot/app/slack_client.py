"""Minimal Slack Web API client for posting a worker result in the event thread."""

import os

import httpx


class SlackDeliveryError(RuntimeError):
    """Slack did not accept a response posted by the worker."""


async def post_thread_reply(*, channel: str, thread_ts: str, text: str) -> None:
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    if not token:
        raise SlackDeliveryError("SLACK_BOT_TOKEN is not configured.")
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                json={"channel": channel, "thread_ts": thread_ts, "text": text},
            )
            response.raise_for_status()
            result = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise SlackDeliveryError("Slack reply delivery failed.") from exc
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise SlackDeliveryError("Slack reply delivery failed.")
