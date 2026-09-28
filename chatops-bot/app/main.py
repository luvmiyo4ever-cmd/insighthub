"""HTTP entrypoint for the Day 5 ChatOps bot."""

import json
import os

from fastapi import FastAPI, HTTPException, Request

from app.slack_auth import (
    SlackAuthenticationError,
    SlackConfigurationError,
    verify_slack_signature,
)
from app.queue import QueueUnavailable, SlackEventError, build_job, enqueue_event

app = FastAPI(title="InsightHub ChatOps", version="0.2.0")

@app.get("/healthz")
def health() -> dict[str, str]:
    """Liveness only; readiness awaits an authenticated Slack adapter."""
    return {
        "status": "ok",
        "service": "insighthub-chatops-bot",
        "transport": "http",
        "authentication": "not_configured",
    }

@app.post("/slack/events")
async def slack_events(request: Request) -> dict[str, str]:
    """Verify Slack authentication before accepting any event.

    The endpoint only authenticates and durably enqueues app mentions. It does
    not call infrastructure or Slack's Web API before returning its ACK.
    """
    body = await request.body()
    try:
        verify_slack_signature(
            body=body,
            timestamp=request.headers.get("X-Slack-Request-Timestamp"),
            signature=request.headers.get("X-Slack-Signature"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET", ""),
        )
    except SlackConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Slack signature is not configured.") from exc
    except SlackAuthenticationError as exc:
        raise HTTPException(status_code=401, detail="Invalid Slack request signature.") from exc

    try:
        payload = json.loads(body)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Slack request must be valid JSON.") from exc
    if payload.get("type") == "url_verification":
        challenge = payload.get("challenge")
        if not isinstance(challenge, str) or not challenge:
            raise HTTPException(status_code=400, detail="Slack URL verification challenge is invalid.")
        return {"challenge": challenge}

    if not os.environ.get("SLACK_BOT_TOKEN"):
        raise HTTPException(status_code=503, detail="Slack bot delivery is not configured.")
    try:
        job = build_job(payload)
    except SlackEventError as exc:
        raise HTTPException(status_code=400, detail="Slack app mention is invalid.") from exc
    if job is None:
        return {"ok": "true"}
    try:
        await enqueue_event(job)
    except QueueUnavailable as exc:
        raise HTTPException(status_code=503, detail="Slack event queue is unavailable.") from exc
    return {"ok": "true"}
