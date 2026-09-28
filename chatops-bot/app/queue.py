"""Durable, deduplicated dispatch of verified Slack events."""

import os
from collections.abc import Mapping
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings

CHATOPS_QUEUE_NAME = "arq:chatops"


class SlackEventError(ValueError):
    """The signed payload is not a valid app_mention event."""


class QueueUnavailable(RuntimeError):
    """Redis could not durably accept an otherwise valid Slack event."""


def build_job(payload: Mapping[str, Any]) -> dict[str, str] | None:
    """Project Slack input to the smallest job payload needed by the worker."""
    if payload.get("type") != "event_callback":
        return None
    event = payload.get("event")
    if not isinstance(event, Mapping) or event.get("type") != "app_mention":
        return None
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return None

    event_id = payload.get("event_id")
    channel = event.get("channel")
    user = event.get("user")
    text = event.get("text")
    thread_ts = event.get("thread_ts") or event.get("ts")
    fields = (event_id, channel, user, text, thread_ts)
    if not all(isinstance(value, str) and value for value in fields):
        raise SlackEventError("Slack app_mention event is incomplete.")
    return {
        "event_id": event_id,
        "channel": channel,
        "user": user,
        "text": text,
        "thread_ts": thread_ts,
    }


async def enqueue_event(job: Mapping[str, str]) -> bool:
    """Enqueue exactly once per Slack event ID; false means a duplicate."""
    redis = None
    try:
        redis = await create_pool(RedisSettings.from_dsn(os.environ["REDIS_URL"]))
        queued = await redis.enqueue_job(
            "process_slack_event",
            dict(job),
            _job_id=f"slack:{job['event_id']}",
            _queue_name=CHATOPS_QUEUE_NAME,
        )
        return queued is not None
    except Exception as exc:
        raise QueueUnavailable("Slack event queue is unavailable.") from exc
    finally:
        if redis is not None:
            await redis.aclose()
